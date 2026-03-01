"""
Cross-Ledger Consistency Protocol — Reference Implementation

Closes Gap #1 from FEDERATION_DOCUMENTATION_GAPS.md.

When multiple societies in a federation maintain independent ledgers,
this protocol ensures:
1. Fork detection: Divergent block histories identified via anchor comparison
2. ATP-safe reconciliation: Conservation-preserving balance sync (NOT CRDTs)
3. Cross-ledger atomicity: Two-phase commit spanning ledger boundaries
4. Epoch-based anchoring: Agreed-upon snapshot intervals for comparison
5. Federation governance quorum: N-party consensus for cross-ledger decisions

Key design tension resolved:
- CRDTs work for trust (monotonic merge). ATP requires conservation.
- This protocol uses epoch-anchored bilateral proofs aggregated into
  a federation-wide consistency certificate, NOT CRDTs for ATP.

Builds on:
- federation_consensus_atp.py (ATPLedger, 2PC, FBPBFT)
- cross_society_atp_sync.py (BalanceProof, BilateralStatement)
- network_partition_recovery.py (LedgerAnchor, vector clocks)
- gossip_protocol_federation.py (gossip dissemination)
- adaptive_consensus_protocol.py (consensus switching)

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
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Core Types ───────────────────────────────────────────────────────────────

class LedgerStatus(Enum):
    CONSISTENT = auto()     # Matches federation anchor
    DIVERGED = auto()       # Hash mismatch at epoch boundary
    PARTITIONED = auto()    # Unreachable for anchor exchange
    RECOVERING = auto()     # Reconciliation in progress
    FORKED = auto()         # Incompatible histories detected


class ReconciliationStrategy(Enum):
    CONSERVATIVE = auto()   # Use minimum balances (safe for ATP)
    AUTHORITATIVE = auto()  # Higher-trust ledger wins
    BILATERAL = auto()      # Negotiated reconciliation
    ROLLBACK = auto()       # Roll back to last consistent anchor


class CrossLedgerTxPhase(Enum):
    INITIATED = auto()
    SOURCE_LOCKED = auto()
    TARGET_PREPARED = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()
    TIMED_OUT = auto()


class GovernanceDecisionType(Enum):
    PARAMETER_CHANGE = auto()
    MEMBERSHIP_CHANGE = auto()
    POLICY_UPDATE = auto()
    EMERGENCY_FREEZE = auto()
    TREATY_RATIFICATION = auto()


# ─── Ledger Model ────────────────────────────────────────────────────────────

@dataclass
class LedgerEntry:
    """A single ledger entry with hash chain."""
    sequence: int
    entry_type: str  # "transfer", "lock", "commit", "rollback", "governance"
    data: Dict[str, Any]
    timestamp: float
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.sequence}:{self.entry_type}:{self.data}:{self.prev_hash}"
        self.entry_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.entry_hash


@dataclass
class SocietyLedger:
    """A society's local ledger with hash-chained entries."""
    society_id: str
    entries: List[LedgerEntry] = field(default_factory=list)
    balances: Dict[str, float] = field(default_factory=dict)  # entity_id -> ATP balance
    total_supply: float = 10000.0
    total_fees: float = 0.0
    cross_ledger_outflow: float = 0.0   # ATP sent to other ledgers (net)
    cross_ledger_inflow: float = 0.0    # ATP received from other ledgers (net)
    sequence: int = 0

    @property
    def head_hash(self) -> str:
        return self.entries[-1].entry_hash if self.entries else "genesis"

    @property
    def conservation_check(self) -> float:
        """Sum of all balances + fees + outflow - inflow should equal total_supply."""
        return sum(self.balances.values()) + self.total_fees + self.cross_ledger_outflow - self.cross_ledger_inflow

    def append_entry(self, entry_type: str, data: Dict[str, Any]) -> LedgerEntry:
        self.sequence += 1
        entry = LedgerEntry(
            sequence=self.sequence,
            entry_type=entry_type,
            data=data,
            timestamp=time.time(),
            prev_hash=self.head_hash,
        )
        entry.compute_hash()
        self.entries.append(entry)
        return entry

    def transfer(self, source: str, target: str, amount: float,
                  fee_rate: float = 0.05) -> Optional[LedgerEntry]:
        """Execute a local transfer with fee."""
        if amount <= 0 or math.isnan(amount):
            return None
        if self.balances.get(source, 0) < amount:
            return None

        fee = amount * fee_rate
        net_amount = amount - fee

        self.balances[source] -= amount
        self.balances[target] = self.balances.get(target, 0) + net_amount
        self.total_fees += fee

        return self.append_entry("transfer", {
            "source": source, "target": target,
            "amount": amount, "fee": fee, "net": net_amount,
        })

    def state_hash(self) -> str:
        """Deterministic hash of current balance state."""
        sorted_balances = sorted(self.balances.items())
        state = f"{self.society_id}:{sorted_balances}:{self.total_fees}"
        return hashlib.sha256(state.encode()).hexdigest()[:32]


# ─── Epoch Anchoring ─────────────────────────────────────────────────────────

@dataclass
class EpochAnchor:
    """A snapshot of ledger state at an epoch boundary."""
    epoch: int
    society_id: str
    sequence_at_epoch: int
    state_hash: str           # Hash of balance state
    head_entry_hash: str      # Hash chain head
    total_supply: float
    total_fees: float
    balance_count: int
    timestamp: float = field(default_factory=time.time)
    signature: str = ""       # Society's signature

    def sign(self, society_id: str) -> str:
        data = f"{self.epoch}:{self.society_id}:{self.state_hash}:{self.head_entry_hash}"
        self.signature = hashlib.sha256(f"{data}:{society_id}".encode()).hexdigest()[:16]
        return self.signature


class EpochManager:
    """Manage epoch boundaries and anchor creation."""

    def __init__(self, epoch_interval: int = 100):
        self.epoch_interval = epoch_interval
        self.current_epoch: int = 0
        self.anchors: Dict[Tuple[int, str], EpochAnchor] = {}  # (epoch, society) -> anchor

    def should_anchor(self, ledger: SocietyLedger) -> bool:
        """Check if it's time for a new anchor."""
        return ledger.sequence > 0 and ledger.sequence % self.epoch_interval == 0

    def create_anchor(self, ledger: SocietyLedger, epoch: int) -> EpochAnchor:
        """Create an anchor from current ledger state."""
        anchor = EpochAnchor(
            epoch=epoch,
            society_id=ledger.society_id,
            sequence_at_epoch=ledger.sequence,
            state_hash=ledger.state_hash(),
            head_entry_hash=ledger.head_hash,
            total_supply=ledger.total_supply,
            total_fees=ledger.total_fees,
            balance_count=len(ledger.balances),
        )
        anchor.sign(ledger.society_id)
        self.anchors[(epoch, ledger.society_id)] = anchor
        return anchor

    def advance_epoch(self) -> int:
        self.current_epoch += 1
        return self.current_epoch

    def get_anchor(self, epoch: int, society_id: str) -> Optional[EpochAnchor]:
        return self.anchors.get((epoch, society_id))


# ─── Fork Detection ─────────────────────────────────────────────────────────

@dataclass
class ForkReport:
    """Report of a detected fork between ledgers."""
    report_id: str
    epoch: int
    society_a: str
    society_b: str
    divergence_type: str    # "state_hash", "supply_mismatch", "sequence_gap"
    severity: float         # 0-1
    details: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class ForkDetector:
    """Detect forks and divergences between society ledgers."""

    def __init__(self, supply_tolerance: float = 0.001):
        self.supply_tolerance = supply_tolerance

    def compare_anchors(self, anchor_a: EpochAnchor,
                         anchor_b: EpochAnchor) -> Optional[ForkReport]:
        """Compare two anchors from the same epoch for consistency."""
        if anchor_a.epoch != anchor_b.epoch:
            return None

        details: Dict[str, Any] = {
            "a_state_hash": anchor_a.state_hash,
            "b_state_hash": anchor_b.state_hash,
            "a_supply": anchor_a.total_supply,
            "b_supply": anchor_b.total_supply,
        }

        # Cross-ledger supply conservation check
        a_total = anchor_a.total_supply
        b_total = anchor_b.total_supply
        supply_diff = abs(a_total - b_total) / max(a_total, b_total, 1)

        if supply_diff > self.supply_tolerance:
            return ForkReport(
                report_id=secrets.token_hex(8),
                epoch=anchor_a.epoch,
                society_a=anchor_a.society_id,
                society_b=anchor_b.society_id,
                divergence_type="supply_mismatch",
                severity=min(supply_diff * 10, 1.0),
                details=details,
            )

        # Sequence gap detection
        seq_gap = abs(anchor_a.sequence_at_epoch - anchor_b.sequence_at_epoch)
        if seq_gap > 50:
            details["sequence_gap"] = seq_gap
            return ForkReport(
                report_id=secrets.token_hex(8),
                epoch=anchor_a.epoch,
                society_a=anchor_a.society_id,
                society_b=anchor_b.society_id,
                divergence_type="sequence_gap",
                severity=min(seq_gap / 200, 1.0),
                details=details,
            )

        return None

    def detect_internal_fork(self, ledger: SocietyLedger) -> Optional[ForkReport]:
        """Check a single ledger for internal consistency issues."""
        # Conservation check
        actual = ledger.conservation_check
        diff = abs(actual - ledger.total_supply)

        if diff > self.supply_tolerance:
            return ForkReport(
                report_id=secrets.token_hex(8),
                epoch=0,
                society_a=ledger.society_id,
                society_b=ledger.society_id,
                divergence_type="conservation_violation",
                severity=min(diff / ledger.total_supply, 1.0),
                details={"expected": ledger.total_supply, "actual": actual, "diff": diff},
            )

        # Hash chain integrity
        for i in range(1, len(ledger.entries)):
            if ledger.entries[i].prev_hash != ledger.entries[i - 1].entry_hash:
                return ForkReport(
                    report_id=secrets.token_hex(8),
                    epoch=0,
                    society_a=ledger.society_id,
                    society_b=ledger.society_id,
                    divergence_type="hash_chain_broken",
                    severity=1.0,
                    details={"broken_at_seq": ledger.entries[i].sequence},
                )

        return None


# ─── Cross-Ledger Atomic Transaction ────────────────────────────────────────

@dataclass
class CrossLedgerTransaction:
    """A two-phase commit transaction spanning two ledgers."""
    tx_id: str
    source_society: str
    target_society: str
    source_entity: str
    target_entity: str
    amount: float
    fee_rate: float = 0.05
    phase: CrossLedgerTxPhase = CrossLedgerTxPhase.INITIATED
    lock_entry_seq: int = 0
    prepare_entry_seq: int = 0
    commit_entry_seq: int = 0
    timeout: float = 30.0
    created_at: float = field(default_factory=time.time)

    @property
    def is_timed_out(self) -> bool:
        return time.time() - self.created_at > self.timeout


class CrossLedgerCommitProtocol:
    """
    Two-phase commit for cross-ledger transactions.

    Phase 1: Lock on source ledger (debit + lock entry)
    Phase 2: Prepare on target ledger (credit reserve entry)
    Phase 3: Commit on both (finalize entries)

    If any phase fails: rollback all changes.
    """

    def __init__(self):
        self.pending: Dict[str, CrossLedgerTransaction] = {}
        self.completed: List[CrossLedgerTransaction] = []

    def initiate(self, source_ledger: SocietyLedger,
                  target_ledger: SocietyLedger,
                  source_entity: str, target_entity: str,
                  amount: float) -> CrossLedgerTransaction:
        """Start a cross-ledger transaction."""
        tx = CrossLedgerTransaction(
            tx_id=secrets.token_hex(8),
            source_society=source_ledger.society_id,
            target_society=target_ledger.society_id,
            source_entity=source_entity,
            target_entity=target_entity,
            amount=amount,
        )
        self.pending[tx.tx_id] = tx
        return tx

    def phase1_lock(self, tx: CrossLedgerTransaction,
                     source_ledger: SocietyLedger) -> bool:
        """Phase 1: Lock funds on source ledger."""
        if source_ledger.balances.get(tx.source_entity, 0) < tx.amount:
            tx.phase = CrossLedgerTxPhase.ROLLED_BACK
            return False

        # Debit source
        source_ledger.balances[tx.source_entity] -= tx.amount
        fee = tx.amount * tx.fee_rate
        net_amount = tx.amount - fee
        source_ledger.total_fees += fee
        source_ledger.cross_ledger_outflow += net_amount  # Track outflow

        entry = source_ledger.append_entry("cross_lock", {
            "tx_id": tx.tx_id,
            "source": tx.source_entity,
            "amount": tx.amount,
            "fee": fee,
            "target_society": tx.target_society,
        })
        tx.lock_entry_seq = entry.sequence
        tx.phase = CrossLedgerTxPhase.SOURCE_LOCKED
        return True

    def phase2_prepare(self, tx: CrossLedgerTransaction,
                        target_ledger: SocietyLedger) -> bool:
        """Phase 2: Prepare credit on target ledger."""
        if tx.phase != CrossLedgerTxPhase.SOURCE_LOCKED:
            return False

        net_amount = tx.amount * (1 - tx.fee_rate)
        target_ledger.balances[tx.target_entity] = (
            target_ledger.balances.get(tx.target_entity, 0) + net_amount
        )
        target_ledger.cross_ledger_inflow += net_amount  # Track inflow

        entry = target_ledger.append_entry("cross_prepare", {
            "tx_id": tx.tx_id,
            "target": tx.target_entity,
            "net_amount": net_amount,
            "source_society": tx.source_society,
        })
        tx.prepare_entry_seq = entry.sequence
        tx.phase = CrossLedgerTxPhase.TARGET_PREPARED
        return True

    def phase3_commit(self, tx: CrossLedgerTransaction,
                       source_ledger: SocietyLedger,
                       target_ledger: SocietyLedger) -> bool:
        """Phase 3: Commit on both ledgers."""
        if tx.phase != CrossLedgerTxPhase.TARGET_PREPARED:
            return False

        source_ledger.append_entry("cross_commit", {
            "tx_id": tx.tx_id, "role": "source"})
        target_ledger.append_entry("cross_commit", {
            "tx_id": tx.tx_id, "role": "target"})

        tx.phase = CrossLedgerTxPhase.COMMITTED
        del self.pending[tx.tx_id]
        self.completed.append(tx)
        return True

    def rollback(self, tx: CrossLedgerTransaction,
                  source_ledger: SocietyLedger,
                  target_ledger: SocietyLedger) -> bool:
        """Rollback a failed transaction."""
        if tx.phase == CrossLedgerTxPhase.COMMITTED:
            return False

        if tx.phase in (CrossLedgerTxPhase.SOURCE_LOCKED,
                         CrossLedgerTxPhase.TARGET_PREPARED):
            source_ledger.balances[tx.source_entity] = (
                source_ledger.balances.get(tx.source_entity, 0) + tx.amount
            )
            fee = tx.amount * tx.fee_rate
            net_amount_src = tx.amount - fee
            source_ledger.total_fees -= fee
            source_ledger.cross_ledger_outflow -= net_amount_src  # Reverse outflow
            source_ledger.append_entry("cross_rollback", {
                "tx_id": tx.tx_id, "role": "source", "restored": tx.amount})

        if tx.phase == CrossLedgerTxPhase.TARGET_PREPARED:
            net_amount = tx.amount * (1 - tx.fee_rate)
            target_ledger.balances[tx.target_entity] = (
                target_ledger.balances.get(tx.target_entity, 0) - net_amount
            )
            target_ledger.cross_ledger_inflow -= net_amount  # Reverse inflow
            target_ledger.append_entry("cross_rollback", {
                "tx_id": tx.tx_id, "role": "target", "removed": net_amount})

        tx.phase = CrossLedgerTxPhase.ROLLED_BACK
        if tx.tx_id in self.pending:
            del self.pending[tx.tx_id]
        return True

    def execute_atomic(self, source_ledger: SocietyLedger,
                        target_ledger: SocietyLedger,
                        source_entity: str, target_entity: str,
                        amount: float) -> CrossLedgerTransaction:
        """Execute a full atomic cross-ledger transaction."""
        tx = self.initiate(source_ledger, target_ledger,
                            source_entity, target_entity, amount)

        if not self.phase1_lock(tx, source_ledger):
            return tx

        if not self.phase2_prepare(tx, target_ledger):
            self.rollback(tx, source_ledger, target_ledger)
            return tx

        self.phase3_commit(tx, source_ledger, target_ledger)
        return tx


# ─── ATP-Safe Reconciliation ────────────────────────────────────────────────

@dataclass
class ReconciliationReport:
    """Report of a cross-ledger reconciliation."""
    report_id: str
    epoch: int
    societies: List[str]
    strategy: ReconciliationStrategy
    adjustments: Dict[str, Dict[str, float]]  # society -> {entity -> adjustment}
    total_adjustment: float
    conservation_before: Dict[str, float]
    conservation_after: Dict[str, float]
    success: bool
    details: str = ""
    timestamp: float = field(default_factory=time.time)


class ATPSafeReconciler:
    """
    Reconcile ATP balances across ledgers while preserving conservation.

    Key insight: CRDTs don't work for ATP because they allow value creation.
    Instead, use conservative reconciliation:
    - When in doubt, use the LOWER balance (prevents inflation)
    - Differences go to fees (preserves conservation)
    - Each ledger's total_supply is immutable; only balances shift
    """

    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def reconcile_pair(self, ledger_a: SocietyLedger,
                        ledger_b: SocietyLedger,
                        shared_entities: Set[str],
                        strategy: ReconciliationStrategy = ReconciliationStrategy.CONSERVATIVE
                        ) -> ReconciliationReport:
        """Reconcile shared entity balances between two ledgers."""
        adjustments_a: Dict[str, float] = {}
        adjustments_b: Dict[str, float] = {}
        total_adj = 0.0

        conservation_before = {
            ledger_a.society_id: ledger_a.conservation_check,
            ledger_b.society_id: ledger_b.conservation_check,
        }

        for entity_id in shared_entities:
            bal_a = ledger_a.balances.get(entity_id, 0)
            bal_b = ledger_b.balances.get(entity_id, 0)

            if abs(bal_a - bal_b) <= self.tolerance:
                continue

            if strategy == ReconciliationStrategy.CONSERVATIVE:
                agreed = min(bal_a, bal_b)
            elif strategy == ReconciliationStrategy.AUTHORITATIVE:
                if ledger_a.total_supply >= ledger_b.total_supply:
                    agreed = bal_a
                else:
                    agreed = bal_b
            elif strategy == ReconciliationStrategy.BILATERAL:
                agreed = (bal_a + bal_b) / 2
            else:
                agreed = min(bal_a, bal_b)

            diff_a = bal_a - agreed
            diff_b = bal_b - agreed

            if abs(diff_a) > self.tolerance:
                adjustments_a[entity_id] = -diff_a
                ledger_a.balances[entity_id] = agreed
                ledger_a.total_fees += diff_a
                total_adj += abs(diff_a)

            if abs(diff_b) > self.tolerance:
                adjustments_b[entity_id] = -diff_b
                ledger_b.balances[entity_id] = agreed
                ledger_b.total_fees += diff_b
                total_adj += abs(diff_b)

        conservation_after = {
            ledger_a.society_id: ledger_a.conservation_check,
            ledger_b.society_id: ledger_b.conservation_check,
        }

        success = all(
            abs(conservation_after[s] - conservation_before[s]) < self.tolerance
            for s in conservation_before
        )

        return ReconciliationReport(
            report_id=secrets.token_hex(8),
            epoch=0,
            societies=[ledger_a.society_id, ledger_b.society_id],
            strategy=strategy,
            adjustments={ledger_a.society_id: adjustments_a,
                          ledger_b.society_id: adjustments_b},
            total_adjustment=total_adj,
            conservation_before=conservation_before,
            conservation_after=conservation_after,
            success=success,
        )


# ─── Federation Governance Quorum ────────────────────────────────────────────

@dataclass
class GovernanceProposal:
    """A proposal requiring cross-ledger governance consensus."""
    proposal_id: str
    proposer_society: str
    decision_type: GovernanceDecisionType
    parameters: Dict[str, Any]
    votes: Dict[str, bool] = field(default_factory=dict)
    required_quorum: float = 0.67
    trust_weights: Dict[str, float] = field(default_factory=dict)
    status: str = "PENDING"
    timestamp: float = field(default_factory=time.time)

    @property
    def weighted_approval(self) -> float:
        if not self.votes:
            return 0.0
        total_weight = sum(self.trust_weights.get(s, 1.0) for s in self.votes)
        if total_weight == 0:
            return 0.0
        approval_weight = sum(
            self.trust_weights.get(s, 1.0)
            for s, v in self.votes.items() if v
        )
        return approval_weight / total_weight

    @property
    def has_quorum(self) -> bool:
        return self.weighted_approval >= self.required_quorum


class FederationGovernance:
    """N-party governance consensus for cross-ledger decisions."""

    def __init__(self, member_societies: List[str],
                  trust_scores: Dict[str, float]):
        self.members = member_societies
        self.trust_scores = trust_scores
        self.proposals: List[GovernanceProposal] = []
        self.decisions: List[GovernanceProposal] = []

    def propose(self, proposer: str,
                 decision_type: GovernanceDecisionType,
                 parameters: Dict[str, Any]) -> GovernanceProposal:
        if proposer not in self.members:
            raise ValueError(f"Non-member {proposer} cannot propose")

        proposal = GovernanceProposal(
            proposal_id=secrets.token_hex(8),
            proposer_society=proposer,
            decision_type=decision_type,
            parameters=parameters,
            trust_weights={s: self.trust_scores.get(s, 1.0) for s in self.members},
        )
        self.proposals.append(proposal)
        return proposal

    def vote(self, proposal: GovernanceProposal,
              society: str, approve: bool) -> bool:
        if society not in self.members:
            return False
        if proposal.status != "PENDING":
            return False
        proposal.votes[society] = approve
        return True

    def finalize(self, proposal: GovernanceProposal) -> str:
        if proposal.has_quorum:
            proposal.status = "APPROVED"
        elif len(proposal.votes) >= len(self.members):
            proposal.status = "REJECTED"

        if proposal.status in ("APPROVED", "REJECTED"):
            self.decisions.append(proposal)

        return proposal.status

    def emergency_freeze(self, proposer: str,
                           reason: str) -> GovernanceProposal:
        proposal = self.propose(proposer, GovernanceDecisionType.EMERGENCY_FREEZE,
                                 {"reason": reason})
        self.vote(proposal, proposer, True)
        return proposal


# ─── Consistency Certificate ─────────────────────────────────────────────────

@dataclass
class ConsistencyCertificate:
    """Federation-wide consistency certificate."""
    cert_id: str
    epoch: int
    society_anchors: Dict[str, EpochAnchor]
    federation_hash: str
    total_federation_supply: float
    total_federation_fees: float
    all_consistent: bool
    fork_reports: List[ForkReport]
    timestamp: float = field(default_factory=time.time)
    signatures: Dict[str, str] = field(default_factory=dict)

    @property
    def society_count(self) -> int:
        return len(self.society_anchors)


class ConsistencyCertifier:
    """Generate federation-wide consistency certificates."""

    def __init__(self, fork_detector: ForkDetector):
        self.fork_detector = fork_detector
        self.certificates: List[ConsistencyCertificate] = []

    def certify_epoch(self, epoch: int,
                       anchors: Dict[str, EpochAnchor]) -> ConsistencyCertificate:
        fork_reports = []

        society_ids = list(anchors.keys())
        for i in range(len(society_ids)):
            for j in range(i + 1, len(society_ids)):
                report = self.fork_detector.compare_anchors(
                    anchors[society_ids[i]], anchors[society_ids[j]])
                if report:
                    fork_reports.append(report)

        sorted_hashes = sorted(
            f"{sid}:{a.state_hash}" for sid, a in anchors.items())
        federation_hash = hashlib.sha256(
            ":".join(sorted_hashes).encode()).hexdigest()[:32]

        total_supply = sum(a.total_supply for a in anchors.values())
        total_fees = sum(a.total_fees for a in anchors.values())

        cert = ConsistencyCertificate(
            cert_id=secrets.token_hex(8),
            epoch=epoch,
            society_anchors=anchors,
            federation_hash=federation_hash,
            total_federation_supply=total_supply,
            total_federation_fees=total_fees,
            all_consistent=len(fork_reports) == 0,
            fork_reports=fork_reports,
        )

        for sid in anchors:
            cert.signatures[sid] = hashlib.sha256(
                f"{cert.cert_id}:{sid}:{federation_hash}".encode()
            ).hexdigest()[:16]

        self.certificates.append(cert)
        return cert


# ─── Full Protocol Orchestrator ──────────────────────────────────────────────

class CrossLedgerProtocol:
    """
    Orchestrates the complete cross-ledger consistency protocol.

    Workflow:
    1. Each society operates its own ledger
    2. Cross-ledger transactions use 2PC
    3. At epoch boundaries, anchors are created and compared
    4. Forks trigger reconciliation
    5. Federation governance uses N-party consensus
    """

    def __init__(self, epoch_interval: int = 10):
        self.epoch_manager = EpochManager(epoch_interval)
        self.fork_detector = ForkDetector()
        self.commit_protocol = CrossLedgerCommitProtocol()
        self.reconciler = ATPSafeReconciler()
        self.certifier = ConsistencyCertifier(self.fork_detector)
        self.ledgers: Dict[str, SocietyLedger] = {}
        self.governance: Optional[FederationGovernance] = None

    def register_society(self, society_id: str, initial_supply: float = 10000.0,
                           initial_entities: Optional[Dict[str, float]] = None) -> SocietyLedger:
        ledger = SocietyLedger(
            society_id=society_id,
            total_supply=initial_supply,
        )
        if initial_entities:
            for eid, balance in initial_entities.items():
                ledger.balances[eid] = balance
        allocated = sum(ledger.balances.values())
        if allocated < initial_supply:
            ledger.balances[f"{society_id}_reserve"] = initial_supply - allocated

        self.ledgers[society_id] = ledger
        return ledger

    def setup_governance(self, trust_scores: Dict[str, float]):
        self.governance = FederationGovernance(
            list(self.ledgers.keys()), trust_scores)

    def cross_transfer(self, source_society: str, target_society: str,
                        source_entity: str, target_entity: str,
                        amount: float) -> CrossLedgerTransaction:
        source_ledger = self.ledgers[source_society]
        target_ledger = self.ledgers[target_society]
        return self.commit_protocol.execute_atomic(
            source_ledger, target_ledger,
            source_entity, target_entity, amount)

    def epoch_checkpoint(self) -> Optional[ConsistencyCertificate]:
        epoch = self.epoch_manager.advance_epoch()
        anchors = {}
        for sid, ledger in self.ledgers.items():
            anchor = self.epoch_manager.create_anchor(ledger, epoch)
            anchors[sid] = anchor
        return self.certifier.certify_epoch(epoch, anchors)

    def full_consistency_check(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "internal_forks": [],
            "cross_forks": [],
            "conservation": {},
        }

        for sid, ledger in self.ledgers.items():
            report = self.fork_detector.detect_internal_fork(ledger)
            if report:
                results["internal_forks"].append(report)
            results["conservation"][sid] = {
                "expected": ledger.total_supply,
                "actual": ledger.conservation_check,
                "diff": abs(ledger.conservation_check - ledger.total_supply),
            }

        return results


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

    # ── Section 1: Ledger Basics ─────────────────────────────────────────────

    ledger = SocietyLedger(society_id="alpha", total_supply=10000.0)
    ledger.balances = {"alice": 5000.0, "bob": 3000.0, "alpha_reserve": 2000.0}

    check("s1_conservation", abs(ledger.conservation_check - 10000.0) < 0.001,
          f"check={ledger.conservation_check}")
    check("s1_head_hash_genesis", ledger.head_hash == "genesis")

    entry = ledger.transfer("alice", "bob", 100.0, fee_rate=0.05)
    check("s1_transfer_success", entry is not None)
    check("s1_alice_debited", ledger.balances["alice"] == 4900.0,
          f"bal={ledger.balances['alice']}")
    check("s1_bob_credited", ledger.balances["bob"] == 3095.0,
          f"bal={ledger.balances['bob']}")
    check("s1_fee_collected", abs(ledger.total_fees - 5.0) < 0.001,
          f"fees={ledger.total_fees}")
    check("s1_conservation_after", abs(ledger.conservation_check - 10000.0) < 0.001)
    check("s1_hash_chain", ledger.head_hash != "genesis")
    check("s1_sequence", ledger.sequence == 1)

    check("s1_insufficient_funds", ledger.transfer("alice", "bob", 99999) is None)
    check("s1_negative_amount", ledger.transfer("alice", "bob", -100) is None)
    check("s1_nan_amount", ledger.transfer("alice", "bob", float('nan')) is None)

    # ── Section 2: State Hash ────────────────────────────────────────────────

    hash1 = ledger.state_hash()
    check("s2_state_hash_nonempty", len(hash1) == 32)
    hash2 = ledger.state_hash()
    check("s2_deterministic", hash1 == hash2)
    ledger.transfer("alice", "bob", 10.0)
    hash3 = ledger.state_hash()
    check("s2_changes_on_transfer", hash3 != hash1)

    # ── Section 3: Epoch Anchoring ───────────────────────────────────────────

    em = EpochManager(epoch_interval=5)
    test_ledger = SocietyLedger(society_id="beta", total_supply=5000.0)
    test_ledger.balances = {"carol": 3000.0, "dave": 2000.0}

    check("s3_no_anchor_at_0", not em.should_anchor(test_ledger))

    for i in range(5):
        test_ledger.transfer("carol", "dave", 10.0)
    check("s3_anchor_at_5", em.should_anchor(test_ledger))

    epoch = em.advance_epoch()
    anchor = em.create_anchor(test_ledger, epoch)
    check("s3_anchor_epoch", anchor.epoch == 1)
    check("s3_anchor_society", anchor.society_id == "beta")
    check("s3_anchor_signed", len(anchor.signature) == 16)
    check("s3_anchor_state_hash", len(anchor.state_hash) == 32)
    check("s3_anchor_stored", em.get_anchor(1, "beta") is anchor)

    # ── Section 4: Fork Detection — Internal ─────────────────────────────────

    fd = ForkDetector()

    healthy = SocietyLedger(society_id="healthy", total_supply=1000.0)
    healthy.balances = {"x": 500.0, "y": 500.0}
    check("s4_no_internal_fork", fd.detect_internal_fork(healthy) is None)

    violated = SocietyLedger(society_id="violated", total_supply=1000.0)
    violated.balances = {"x": 600.0, "y": 500.0}
    report = fd.detect_internal_fork(violated)
    check("s4_conservation_fork", report is not None)
    check("s4_fork_type", report.divergence_type == "conservation_violation"
          if report else False)

    broken = SocietyLedger(society_id="broken", total_supply=1000.0)
    broken.balances = {"x": 500.0, "y": 500.0}
    broken.transfer("x", "y", 10.0)
    broken.transfer("x", "y", 10.0)
    broken.entries[1].prev_hash = "tampered"
    report2 = fd.detect_internal_fork(broken)
    check("s4_hash_chain_fork", report2 is not None)
    check("s4_hash_chain_type", report2.divergence_type == "hash_chain_broken"
          if report2 else False)

    # ── Section 5: Fork Detection — Cross-Ledger ─────────────────────────────

    anchor_a = EpochAnchor(epoch=1, society_id="a", sequence_at_epoch=100,
                            state_hash="abc123", head_entry_hash="h1",
                            total_supply=10000.0, total_fees=50.0, balance_count=10)
    anchor_b = EpochAnchor(epoch=1, society_id="b", sequence_at_epoch=100,
                            state_hash="def456", head_entry_hash="h2",
                            total_supply=10000.0, total_fees=60.0, balance_count=10)

    cross_report = fd.compare_anchors(anchor_a, anchor_b)
    check("s5_no_supply_fork", cross_report is None)

    anchor_c = EpochAnchor(epoch=1, society_id="c", sequence_at_epoch=100,
                            state_hash="ghi789", head_entry_hash="h3",
                            total_supply=15000.0, total_fees=0, balance_count=10)
    supply_report = fd.compare_anchors(anchor_a, anchor_c)
    check("s5_supply_fork_detected", supply_report is not None)
    check("s5_supply_fork_type", supply_report.divergence_type == "supply_mismatch"
          if supply_report else False)

    anchor_d = EpochAnchor(epoch=1, society_id="d", sequence_at_epoch=200,
                            state_hash="jkl012", head_entry_hash="h4",
                            total_supply=10000.0, total_fees=0, balance_count=10)
    gap_report = fd.compare_anchors(anchor_a, anchor_d)
    check("s5_sequence_gap", gap_report is not None)
    check("s5_gap_type", gap_report.divergence_type == "sequence_gap"
          if gap_report else False)

    # ── Section 6: Cross-Ledger 2PC — Success ───────────────────────────────

    source = SocietyLedger(society_id="source", total_supply=5000.0)
    source.balances = {"alice": 2500.0, "source_reserve": 2500.0}
    target = SocietyLedger(society_id="target", total_supply=5000.0)
    target.balances = {"bob": 2000.0, "target_reserve": 3000.0}

    clcp = CrossLedgerCommitProtocol()
    tx = clcp.execute_atomic(source, target, "alice", "bob", 100.0)

    check("s6_tx_committed", tx.phase == CrossLedgerTxPhase.COMMITTED,
          f"phase={tx.phase}")
    check("s6_alice_debited", source.balances["alice"] == 2400.0,
          f"bal={source.balances['alice']}")
    check("s6_bob_credited", target.balances["bob"] == 2095.0,
          f"bal={target.balances['bob']}")
    check("s6_source_fee", abs(source.total_fees - 5.0) < 0.001)
    check("s6_source_conservation",
          abs(source.conservation_check - 5000.0) < 0.001,
          f"check={source.conservation_check}")

    # ── Section 7: Cross-Ledger 2PC — Insufficient Funds ────────────────────

    tx_fail = clcp.execute_atomic(source, target, "alice", "bob", 99999.0)
    check("s7_insufficient_rollback",
          tx_fail.phase == CrossLedgerTxPhase.ROLLED_BACK,
          f"phase={tx_fail.phase}")
    check("s7_alice_unchanged", source.balances["alice"] == 2400.0)

    # ── Section 8: Cross-Ledger 2PC — Explicit Rollback ─────────────────────

    tx_rb = clcp.initiate(source, target, "alice", "bob", 50.0)
    clcp.phase1_lock(tx_rb, source)
    check("s8_locked", tx_rb.phase == CrossLedgerTxPhase.SOURCE_LOCKED)
    check("s8_alice_after_lock", source.balances["alice"] == 2350.0)

    clcp.phase2_prepare(tx_rb, target)
    check("s8_prepared", tx_rb.phase == CrossLedgerTxPhase.TARGET_PREPARED)

    clcp.rollback(tx_rb, source, target)
    check("s8_rolled_back", tx_rb.phase == CrossLedgerTxPhase.ROLLED_BACK)
    check("s8_alice_restored", source.balances["alice"] == 2400.0,
          f"bal={source.balances['alice']}")

    # ── Section 9: ATP-Safe Reconciliation ───────────────────────────────────

    rec = ATPSafeReconciler()

    ledger_x = SocietyLedger(society_id="x", total_supply=1000.0)
    ledger_x.balances = {"shared1": 300.0, "shared2": 200.0, "x_only": 500.0}
    ledger_y = SocietyLedger(society_id="y", total_supply=1000.0)
    ledger_y.balances = {"shared1": 250.0, "shared2": 220.0, "y_only": 530.0}

    report = rec.reconcile_pair(ledger_x, ledger_y, {"shared1", "shared2"},
                                  ReconciliationStrategy.CONSERVATIVE)
    check("s9_reconciliation_success", report.success)
    check("s9_shared1_conservative", ledger_x.balances["shared1"] == 250.0,
          f"bal={ledger_x.balances['shared1']}")
    check("s9_shared2_conservative", ledger_y.balances["shared2"] == 200.0,
          f"bal={ledger_y.balances['shared2']}")
    check("s9_x_conservation",
          abs(ledger_x.conservation_check - 1000.0) < 0.01,
          f"check={ledger_x.conservation_check}")
    check("s9_y_conservation",
          abs(ledger_y.conservation_check - 1000.0) < 0.01,
          f"check={ledger_y.conservation_check}")

    # ── Section 10: Federation Governance ────────────────────────────────────

    gov = FederationGovernance(
        ["soc_a", "soc_b", "soc_c"],
        {"soc_a": 0.8, "soc_b": 0.6, "soc_c": 0.7},
    )

    proposal = gov.propose("soc_a", GovernanceDecisionType.PARAMETER_CHANGE,
                             {"param": "epoch_interval", "value": 50})
    check("s10_proposal_created", proposal.status == "PENDING")

    gov.vote(proposal, "soc_a", True)
    gov.vote(proposal, "soc_b", True)
    check("s10_two_votes", len(proposal.votes) == 2)
    check("s10_weighted_approval", proposal.weighted_approval > 0.5,
          f"approval={proposal.weighted_approval}")

    check("s10_non_member_rejected", not gov.vote(proposal, "outsider", True))

    gov.vote(proposal, "soc_c", True)
    status = gov.finalize(proposal)
    check("s10_approved", status == "APPROVED")

    p2 = gov.propose("soc_b", GovernanceDecisionType.POLICY_UPDATE,
                       {"policy": "data_sharing"})
    gov.vote(p2, "soc_a", False)
    gov.vote(p2, "soc_b", True)
    gov.vote(p2, "soc_c", False)
    status2 = gov.finalize(p2)
    check("s10_rejected", status2 == "REJECTED")

    # ── Section 11: Emergency Freeze ─────────────────────────────────────────

    freeze = gov.emergency_freeze("soc_a", "Suspicious cross-ledger activity")
    check("s11_freeze_created",
          freeze.decision_type == GovernanceDecisionType.EMERGENCY_FREEZE)
    check("s11_auto_voted", "soc_a" in freeze.votes)
    check("s11_pending", freeze.status == "PENDING")

    gov.vote(freeze, "soc_b", True)
    gov.vote(freeze, "soc_c", True)
    status3 = gov.finalize(freeze)
    check("s11_freeze_approved", status3 == "APPROVED")

    # ── Section 12: Consistency Certificate ──────────────────────────────────

    certifier = ConsistencyCertifier(ForkDetector())
    anchors = {
        "soc1": EpochAnchor(epoch=5, society_id="soc1", sequence_at_epoch=50,
                             state_hash="aaa", head_entry_hash="h1",
                             total_supply=10000, total_fees=100, balance_count=5),
        "soc2": EpochAnchor(epoch=5, society_id="soc2", sequence_at_epoch=50,
                             state_hash="bbb", head_entry_hash="h2",
                             total_supply=10000, total_fees=120, balance_count=5),
    }

    cert = certifier.certify_epoch(5, anchors)
    check("s12_cert_created", cert.cert_id != "")
    check("s12_all_consistent", cert.all_consistent)
    check("s12_no_forks", len(cert.fork_reports) == 0)
    check("s12_federation_hash", len(cert.federation_hash) == 32)
    check("s12_total_supply", cert.total_federation_supply == 20000)
    check("s12_signatures", len(cert.signatures) == 2)
    check("s12_society_count", cert.society_count == 2)

    anchors_forked = {
        "soc1": EpochAnchor(epoch=6, society_id="soc1", sequence_at_epoch=60,
                             state_hash="x", head_entry_hash="h1",
                             total_supply=10000, total_fees=0, balance_count=5),
        "soc3": EpochAnchor(epoch=6, society_id="soc3", sequence_at_epoch=60,
                             state_hash="y", head_entry_hash="h3",
                             total_supply=15000, total_fees=0, balance_count=5),
    }
    cert_fork = certifier.certify_epoch(6, anchors_forked)
    check("s12_fork_detected", not cert_fork.all_consistent)
    check("s12_fork_report", len(cert_fork.fork_reports) > 0)

    # ── Section 13: Full Protocol Orchestrator ───────────────────────────────

    proto = CrossLedgerProtocol(epoch_interval=5)
    proto.register_society("alpha", 10000.0, {"alice": 5000, "bob": 3000})
    proto.register_society("beta", 8000.0, {"carol": 4000, "dave": 2000})

    check("s13_societies_registered", len(proto.ledgers) == 2)
    check("s13_alpha_conservation",
          abs(proto.ledgers["alpha"].conservation_check - 10000) < 0.01)
    check("s13_beta_conservation",
          abs(proto.ledgers["beta"].conservation_check - 8000) < 0.01)

    tx = proto.cross_transfer("alpha", "beta", "alice", "carol", 200.0)
    check("s13_cross_transfer_committed",
          tx.phase == CrossLedgerTxPhase.COMMITTED)

    cert = proto.epoch_checkpoint()
    check("s13_cert_generated", cert is not None)
    check("s13_cert_societies", cert.society_count == 2 if cert else False)

    consistency = proto.full_consistency_check()
    check("s13_no_internal_forks", len(consistency["internal_forks"]) == 0)

    # ── Section 14: Multiple Cross-Transfers ─────────────────────────────────

    for i in range(5):
        proto.cross_transfer("alpha", "beta", "alice", "dave", 50.0)

    alpha_cons = proto.ledgers["alpha"].conservation_check
    beta_cons = proto.ledgers["beta"].conservation_check
    check("s14_alpha_conserved", abs(alpha_cons - 10000) < 0.01,
          f"check={alpha_cons}")
    check("s14_beta_conserved", abs(beta_cons - 8000) < 0.01,
          f"check={beta_cons}")

    # ── Section 15: Governance via Protocol ──────────────────────────────────

    proto.setup_governance({"alpha": 0.8, "beta": 0.7})
    p = proto.governance.propose("alpha", GovernanceDecisionType.PARAMETER_CHANGE,
                                   {"param": "fee_rate", "value": 0.03})
    proto.governance.vote(p, "alpha", True)
    proto.governance.vote(p, "beta", True)
    status = proto.governance.finalize(p)
    check("s15_governance_works", status == "APPROVED")

    # ── Section 16: 3-Society Federation ─────────────────────────────────────

    proto3 = CrossLedgerProtocol(epoch_interval=5)
    proto3.register_society("soc1", 5000.0, {"e1": 2500, "e2": 2500})
    proto3.register_society("soc2", 5000.0, {"e3": 2500, "e4": 2500})
    proto3.register_society("soc3", 5000.0, {"e5": 2500, "e6": 2500})

    proto3.cross_transfer("soc1", "soc2", "e1", "e3", 100)
    proto3.cross_transfer("soc2", "soc3", "e3", "e5", 100)
    proto3.cross_transfer("soc3", "soc1", "e5", "e1", 100)

    for sid in ["soc1", "soc2", "soc3"]:
        cons = proto3.ledgers[sid].conservation_check
        check(f"s16_{sid}_conserved", abs(cons - 5000) < 0.01,
              f"check={cons}")

    cert3 = proto3.epoch_checkpoint()
    check("s16_3society_cert", cert3 is not None)
    check("s16_3society_consistent", cert3.all_consistent if cert3 else False)

    # ── Section 17: Reconciliation Strategies ────────────────────────────────

    lx = SocietyLedger(society_id="rx", total_supply=1000.0)
    lx.balances = {"shared": 400.0, "rx_own": 600.0}
    ly = SocietyLedger(society_id="ry", total_supply=1000.0)
    ly.balances = {"shared": 300.0, "ry_own": 700.0}

    rec_bilateral = ATPSafeReconciler()
    report_bi = rec_bilateral.reconcile_pair(lx, ly, {"shared"},
                                               ReconciliationStrategy.BILATERAL)
    check("s17_bilateral_success", report_bi.success)
    check("s17_bilateral_averaged",
          abs(lx.balances["shared"] - 350.0) < 0.01,
          f"bal={lx.balances['shared']}")

    la = SocietyLedger(society_id="ra", total_supply=2000.0)
    la.balances = {"shared2": 800.0, "ra_own": 1200.0}
    lb = SocietyLedger(society_id="rb", total_supply=1000.0)
    lb.balances = {"shared2": 600.0, "rb_own": 400.0}

    report_auth = rec_bilateral.reconcile_pair(la, lb, {"shared2"},
                                                 ReconciliationStrategy.AUTHORITATIVE)
    check("s17_authoritative_success", report_auth.success)
    check("s17_authoritative_a_wins",
          abs(la.balances["shared2"] - 800.0) < 0.01,
          f"bal={la.balances['shared2']}")

    # ── Section 18: Performance ──────────────────────────────────────────────

    perf_proto = CrossLedgerProtocol(epoch_interval=100)
    perf_proto.register_society("perf_a", 100000.0,
                                  {f"ea_{i}": 100.0 for i in range(100)})
    perf_proto.register_society("perf_b", 100000.0,
                                  {f"eb_{i}": 100.0 for i in range(100)})

    t0 = time.time()
    for i in range(100):
        perf_proto.cross_transfer("perf_a", "perf_b",
                                    f"ea_{i}", f"eb_{i}", 10.0)
    elapsed = time.time() - t0
    check("s18_100_transfers_fast", elapsed < 2.0, f"elapsed={elapsed:.2f}s")

    pa_cons = perf_proto.ledgers["perf_a"].conservation_check
    check("s18_perf_a_conserved", abs(pa_cons - 100000) < 0.01,
          f"check={pa_cons}")

    t0 = time.time()
    for _ in range(10):
        perf_proto.epoch_checkpoint()
    elapsed = time.time() - t0
    check("s18_10_epochs_fast", elapsed < 2.0, f"elapsed={elapsed:.2f}s")

    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Cross-Ledger Consistency Protocol: {passed}/{total} checks passed")
    print(f"{'='*60}")

    if passed < total:
        print("\nFailed checks:")
        for name, result in results.items():
            if result.startswith("FAIL"):
                print(f"  {name}: {result}")

    return passed, total


if __name__ == "__main__":
    run_checks()
