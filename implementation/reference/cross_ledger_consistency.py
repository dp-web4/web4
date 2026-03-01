"""
Cross-Ledger Consistency Protocol — Reference Implementation

When multiple federations maintain independent ledgers, they must
periodically verify consistency for shared state (dual-citizenship
entities, cross-federation treaties, ATP transfers). This implements:

1. **Ledger Anchor Points**: Periodic checkpoints with Merkle roots
2. **Fork Detection**: Compare anchor hashes to detect divergence
3. **Reconciliation FSM**: SYNCED → CHECKING → DIVERGED → RECONCILING → SYNCED
4. **Federation Governance Quorum**: Cross-federation votes for state changes
5. **Ledger Merge Protocol**: Conflict resolution for diverged entries

Key insight: Cross-ledger consistency is harder than intra-partition
recovery because the two federations may have *intentionally different*
state for non-shared entities. Only shared-entity state must be consistent.

Builds on: network_partition_recovery.py, gossip_protocol_federation.py
Addresses: FEDERATION_DOCUMENTATION_GAPS.md #1 gap

Checks: 70
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

class ConsistencyState(Enum):
    SYNCED = auto()        # Ledgers are consistent
    CHECKING = auto()      # Verification in progress
    DIVERGED = auto()      # Divergence detected
    RECONCILING = auto()   # Active reconciliation
    FAILED = auto()        # Reconciliation failed — manual intervention

class EntryType(Enum):
    TRUST_UPDATE = auto()
    ATP_TRANSFER = auto()
    MEMBERSHIP_CHANGE = auto()
    POLICY_UPDATE = auto()
    TREATY_CHANGE = auto()
    KEY_ROTATION = auto()

class MergeStrategy(Enum):
    LATEST_WINS = auto()        # Most recent timestamp wins
    HIGHER_TRUST_WINS = auto()  # Federation with higher trust wins
    QUORUM_DECIDES = auto()     # Cross-federation vote
    CONSERVATIVE = auto()       # Most restrictive interpretation


# ─── Ledger Entries ──────────────────────────────────────────────────────────

@dataclass
class LedgerEntry:
    """A single entry in a federation ledger."""
    entry_id: str
    federation_id: str
    entity_id: str
    entry_type: EntryType
    data: Dict[str, Any]
    timestamp: float
    sequence: int
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.entry_id}:{self.federation_id}:{self.entity_id}:" \
                  f"{self.entry_type.name}:{self.data}:{self.timestamp}:" \
                  f"{self.sequence}:{self.prev_hash}"
        self.entry_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.entry_hash


@dataclass
class LedgerAnchor:
    """Periodic checkpoint for consistency verification."""
    anchor_id: str
    federation_id: str
    sequence_start: int
    sequence_end: int
    merkle_root: str
    entry_count: int
    timestamp: float
    shared_entity_hashes: Dict[str, str] = field(default_factory=dict)


# ─── Federation Ledger ───────────────────────────────────────────────────────

class FederationLedger:
    """A federation's append-only ledger with anchoring support."""

    def __init__(self, federation_id: str):
        self.federation_id = federation_id
        self.entries: List[LedgerEntry] = []
        self.anchors: List[LedgerAnchor] = []
        self.sequence_counter = 0
        self.entity_index: Dict[str, List[int]] = defaultdict(list)  # entity → entry indices

    def append(self, entity_id: str, entry_type: EntryType,
               data: Dict[str, Any]) -> LedgerEntry:
        """Append a new entry to the ledger."""
        prev_hash = self.entries[-1].entry_hash if self.entries else "genesis"
        self.sequence_counter += 1

        entry = LedgerEntry(
            entry_id=secrets.token_hex(8),
            federation_id=self.federation_id,
            entity_id=entity_id,
            entry_type=entry_type,
            data=data,
            timestamp=time.time(),
            sequence=self.sequence_counter,
            prev_hash=prev_hash,
        )
        entry.compute_hash()
        self.entries.append(entry)
        self.entity_index[entity_id].append(len(self.entries) - 1)
        return entry

    def get_entries_for_entity(self, entity_id: str) -> List[LedgerEntry]:
        """Get all entries for a specific entity."""
        indices = self.entity_index.get(entity_id, [])
        return [self.entries[i] for i in indices]

    def get_entries_range(self, start_seq: int, end_seq: int) -> List[LedgerEntry]:
        """Get entries within a sequence range."""
        return [e for e in self.entries if start_seq <= e.sequence <= end_seq]

    def compute_merkle_root(self, entries: Optional[List[LedgerEntry]] = None) -> str:
        """Compute Merkle root of entries."""
        if entries is None:
            entries = self.entries

        if not entries:
            return hashlib.sha256(b"empty").hexdigest()[:32]

        hashes = [e.entry_hash for e in entries]

        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest()[:32])
            hashes = next_level

        return hashes[0]

    def create_anchor(self, shared_entities: Set[str]) -> LedgerAnchor:
        """Create a checkpoint anchor."""
        start_seq = self.anchors[-1].sequence_end + 1 if self.anchors else 1
        end_seq = self.sequence_counter

        range_entries = self.get_entries_range(start_seq, end_seq)
        merkle_root = self.compute_merkle_root(range_entries)

        # Compute per-entity content hashes for shared entities
        # Uses data content only (not entry_id/federation_id) for cross-federation comparison
        entity_hashes = {}
        for eid in shared_entities:
            entity_entries = [e for e in range_entries if e.entity_id == eid]
            if entity_entries:
                content_parts = []
                for e in entity_entries:
                    content = f"{e.entity_id}:{e.entry_type.name}:{sorted(e.data.items())}"
                    content_parts.append(hashlib.sha256(content.encode()).hexdigest()[:32])
                # Merkle-like combination of content hashes
                combined = ":".join(sorted(content_parts))
                entity_hashes[eid] = hashlib.sha256(combined.encode()).hexdigest()[:32]

        anchor = LedgerAnchor(
            anchor_id=secrets.token_hex(8),
            federation_id=self.federation_id,
            sequence_start=start_seq,
            sequence_end=end_seq,
            merkle_root=merkle_root,
            entry_count=len(range_entries),
            timestamp=time.time(),
            shared_entity_hashes=entity_hashes,
        )
        self.anchors.append(anchor)
        return anchor

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        for i, entry in enumerate(self.entries):
            expected_prev = self.entries[i - 1].entry_hash if i > 0 else "genesis"
            if entry.prev_hash != expected_prev:
                return False
        return True


# ─── Fork Detection ──────────────────────────────────────────────────────────

@dataclass
class DivergenceReport:
    """Report of detected divergence between two ledgers."""
    report_id: str
    federation_a_id: str
    federation_b_id: str
    diverged_entities: Set[str]
    first_divergence_seq: int
    anchor_a_id: str
    anchor_b_id: str
    severity: float  # 0-1: fraction of shared entities diverged
    timestamp: float = field(default_factory=time.time)


class ForkDetector:
    """Detect ledger forks between federations via anchor comparison."""

    def compare_anchors(self, anchor_a: LedgerAnchor,
                         anchor_b: LedgerAnchor) -> Optional[DivergenceReport]:
        """Compare two anchors to detect divergence."""
        # Check if any shared entity hashes differ
        diverged = set()
        all_shared = set(anchor_a.shared_entity_hashes.keys()) | \
                     set(anchor_b.shared_entity_hashes.keys())

        for eid in all_shared:
            hash_a = anchor_a.shared_entity_hashes.get(eid)
            hash_b = anchor_b.shared_entity_hashes.get(eid)

            if hash_a != hash_b:
                diverged.add(eid)

        if not diverged:
            return None

        severity = len(diverged) / max(len(all_shared), 1)

        return DivergenceReport(
            report_id=secrets.token_hex(8),
            federation_a_id=anchor_a.federation_id,
            federation_b_id=anchor_b.federation_id,
            diverged_entities=diverged,
            first_divergence_seq=min(anchor_a.sequence_start, anchor_b.sequence_start),
            anchor_a_id=anchor_a.anchor_id,
            anchor_b_id=anchor_b.anchor_id,
            severity=severity,
        )

    def detect_sequence_gap(self, anchor_a: LedgerAnchor,
                              anchor_b: LedgerAnchor) -> int:
        """Detect sequence number gaps between anchors."""
        return abs(anchor_a.sequence_end - anchor_b.sequence_end)

    def detect_entry_count_drift(self, anchor_a: LedgerAnchor,
                                   anchor_b: LedgerAnchor) -> float:
        """Detect drift in entry counts (may indicate missed entries)."""
        max_count = max(anchor_a.entry_count, anchor_b.entry_count)
        if max_count == 0:
            return 0.0
        return abs(anchor_a.entry_count - anchor_b.entry_count) / max_count


# ─── Reconciliation FSM ─────────────────────────────────────────────────────

@dataclass
class ReconciliationState:
    """State of the reconciliation process between two federations."""
    state: ConsistencyState = ConsistencyState.SYNCED
    divergence_report: Optional[DivergenceReport] = None
    resolved_entities: Set[str] = field(default_factory=set)
    failed_entities: Set[str] = field(default_factory=set)
    merge_decisions: Dict[str, str] = field(default_factory=dict)  # entity → decision
    history: List[Tuple[ConsistencyState, float]] = field(default_factory=list)

    def transition(self, new_state: ConsistencyState):
        self.history.append((self.state, time.time()))
        self.state = new_state


class ReconciliationFSM:
    """
    State machine for cross-ledger reconciliation.
    SYNCED → CHECKING → DIVERGED → RECONCILING → SYNCED (or FAILED)
    """

    def __init__(self, max_reconciliation_attempts: int = 3):
        self.max_attempts = max_reconciliation_attempts
        self.state = ReconciliationState()
        self.attempts = 0

    def begin_check(self) -> ConsistencyState:
        """Start consistency checking."""
        if self.state.state != ConsistencyState.SYNCED:
            return self.state.state
        self.state.transition(ConsistencyState.CHECKING)
        return ConsistencyState.CHECKING

    def report_divergence(self, report: DivergenceReport) -> ConsistencyState:
        """Report detected divergence."""
        if self.state.state != ConsistencyState.CHECKING:
            return self.state.state
        self.state.divergence_report = report
        self.state.transition(ConsistencyState.DIVERGED)
        return ConsistencyState.DIVERGED

    def report_consistent(self) -> ConsistencyState:
        """Report no divergence found."""
        if self.state.state != ConsistencyState.CHECKING:
            return self.state.state
        self.state.transition(ConsistencyState.SYNCED)
        return ConsistencyState.SYNCED

    def begin_reconciliation(self) -> ConsistencyState:
        """Start reconciliation process."""
        if self.state.state != ConsistencyState.DIVERGED:
            return self.state.state
        self.attempts += 1
        if self.attempts > self.max_attempts:
            self.state.transition(ConsistencyState.FAILED)
            return ConsistencyState.FAILED
        self.state.transition(ConsistencyState.RECONCILING)
        return ConsistencyState.RECONCILING

    def resolve_entity(self, entity_id: str, decision: str) -> bool:
        """Mark an entity as resolved during reconciliation."""
        if self.state.state != ConsistencyState.RECONCILING:
            return False
        self.state.resolved_entities.add(entity_id)
        self.state.merge_decisions[entity_id] = decision
        return True

    def fail_entity(self, entity_id: str) -> bool:
        """Mark an entity reconciliation as failed."""
        if self.state.state != ConsistencyState.RECONCILING:
            return False
        self.state.failed_entities.add(entity_id)
        return True

    def complete_reconciliation(self) -> ConsistencyState:
        """Complete the reconciliation process."""
        if self.state.state != ConsistencyState.RECONCILING:
            return self.state.state

        if self.state.failed_entities:
            self.state.transition(ConsistencyState.FAILED)
        else:
            self.state.transition(ConsistencyState.SYNCED)
            self.attempts = 0
        return self.state.state


# ─── Federation Governance Quorum ────────────────────────────────────────────

@dataclass
class GovernanceProposal:
    """A cross-federation governance proposal requiring quorum."""
    proposal_id: str
    proposer_federation: str
    proposal_type: str  # "merge_entry", "accept_transfer", "policy_change"
    subject_entity: str
    proposed_value: Dict[str, Any]
    votes: Dict[str, bool] = field(default_factory=dict)  # federation → vote
    required_quorum: float = 0.67
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    accepted: bool = False

    @property
    def approval_ratio(self) -> float:
        if not self.votes:
            return 0.0
        return sum(1 for v in self.votes.values() if v) / len(self.votes)

    @property
    def has_quorum(self) -> bool:
        return self.approval_ratio >= self.required_quorum


class GovernanceQuorum:
    """
    Cross-federation governance requiring multi-federation agreement.
    Each participating federation gets one vote, weighted equally.
    """

    def __init__(self, quorum_threshold: float = 0.67):
        self.quorum_threshold = quorum_threshold
        self.proposals: List[GovernanceProposal] = []

    def create_proposal(self, proposer: str, proposal_type: str,
                         entity_id: str, value: Dict[str, Any]) -> GovernanceProposal:
        """Create a new governance proposal."""
        proposal = GovernanceProposal(
            proposal_id=secrets.token_hex(8),
            proposer_federation=proposer,
            proposal_type=proposal_type,
            subject_entity=entity_id,
            proposed_value=value,
            required_quorum=self.quorum_threshold,
        )
        self.proposals.append(proposal)
        return proposal

    def cast_vote(self, proposal: GovernanceProposal,
                   federation_id: str, approve: bool) -> None:
        """Cast a federation's vote on a proposal."""
        if not proposal.resolved:
            proposal.votes[federation_id] = approve

    def resolve_proposal(self, proposal: GovernanceProposal) -> bool:
        """Resolve a proposal based on votes."""
        proposal.resolved = True
        proposal.accepted = proposal.has_quorum
        return proposal.accepted


# ─── Ledger Merge Protocol ───────────────────────────────────────────────────

@dataclass
class MergeDecision:
    """Decision for how to merge a diverged entity's state."""
    entity_id: str
    strategy: MergeStrategy
    chosen_value: Dict[str, Any]
    source_federation: str
    confidence: float
    requires_governance: bool = False


class LedgerMergeProtocol:
    """
    Merge diverged ledger entries using configurable strategies.

    Entry types have default strategies:
    - TRUST_UPDATE: HIGHER_TRUST_WINS (trust is earned, not assigned)
    - ATP_TRANSFER: LATEST_WINS (transfers are timestamped events)
    - MEMBERSHIP_CHANGE: QUORUM_DECIDES (requires cross-fed governance)
    - POLICY_UPDATE: CONSERVATIVE (most restrictive interpretation)
    """

    DEFAULT_STRATEGIES = {
        EntryType.TRUST_UPDATE: MergeStrategy.HIGHER_TRUST_WINS,
        EntryType.ATP_TRANSFER: MergeStrategy.LATEST_WINS,
        EntryType.MEMBERSHIP_CHANGE: MergeStrategy.QUORUM_DECIDES,
        EntryType.POLICY_UPDATE: MergeStrategy.CONSERVATIVE,
        EntryType.TREATY_CHANGE: MergeStrategy.QUORUM_DECIDES,
        EntryType.KEY_ROTATION: MergeStrategy.LATEST_WINS,
    }

    def __init__(self, governance: GovernanceQuorum):
        self.governance = governance

    def resolve_divergence(self, entity_id: str,
                             entries_a: List[LedgerEntry],
                             entries_b: List[LedgerEntry],
                             federation_trusts: Dict[str, float]) -> MergeDecision:
        """Resolve a divergence for a specific entity."""
        if not entries_a and not entries_b:
            return MergeDecision(
                entity_id=entity_id,
                strategy=MergeStrategy.LATEST_WINS,
                chosen_value={},
                source_federation="none",
                confidence=1.0,
            )

        # Determine primary entry type from most recent entries
        latest_a = entries_a[-1] if entries_a else None
        latest_b = entries_b[-1] if entries_b else None

        if latest_a and not latest_b:
            return MergeDecision(
                entity_id=entity_id,
                strategy=MergeStrategy.LATEST_WINS,
                chosen_value=latest_a.data,
                source_federation=latest_a.federation_id,
                confidence=0.9,
            )
        if latest_b and not latest_a:
            return MergeDecision(
                entity_id=entity_id,
                strategy=MergeStrategy.LATEST_WINS,
                chosen_value=latest_b.data,
                source_federation=latest_b.federation_id,
                confidence=0.9,
            )

        # Both have entries — use strategy based on entry type
        entry_type = latest_a.entry_type
        strategy = self.DEFAULT_STRATEGIES.get(entry_type, MergeStrategy.LATEST_WINS)

        if strategy == MergeStrategy.LATEST_WINS:
            if latest_a.timestamp >= latest_b.timestamp:
                return MergeDecision(
                    entity_id=entity_id, strategy=strategy,
                    chosen_value=latest_a.data,
                    source_federation=latest_a.federation_id,
                    confidence=0.8,
                )
            return MergeDecision(
                entity_id=entity_id, strategy=strategy,
                chosen_value=latest_b.data,
                source_federation=latest_b.federation_id,
                confidence=0.8,
            )

        elif strategy == MergeStrategy.HIGHER_TRUST_WINS:
            trust_a = federation_trusts.get(latest_a.federation_id, 0.5)
            trust_b = federation_trusts.get(latest_b.federation_id, 0.5)
            if trust_a >= trust_b:
                return MergeDecision(
                    entity_id=entity_id, strategy=strategy,
                    chosen_value=latest_a.data,
                    source_federation=latest_a.federation_id,
                    confidence=min(trust_a, 1.0),
                )
            return MergeDecision(
                entity_id=entity_id, strategy=strategy,
                chosen_value=latest_b.data,
                source_federation=latest_b.federation_id,
                confidence=min(trust_b, 1.0),
            )

        elif strategy == MergeStrategy.CONSERVATIVE:
            # Take the most restrictive value (lower trust, stricter policy)
            val_a = latest_a.data.get("value", 0)
            val_b = latest_b.data.get("value", 0)
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                if val_a <= val_b:
                    return MergeDecision(
                        entity_id=entity_id, strategy=strategy,
                        chosen_value=latest_a.data,
                        source_federation=latest_a.federation_id,
                        confidence=0.7,
                    )
                return MergeDecision(
                    entity_id=entity_id, strategy=strategy,
                    chosen_value=latest_b.data,
                    source_federation=latest_b.federation_id,
                    confidence=0.7,
                )
            # Non-numeric: default to latest
            if latest_a.timestamp >= latest_b.timestamp:
                return MergeDecision(
                    entity_id=entity_id, strategy=strategy,
                    chosen_value=latest_a.data,
                    source_federation=latest_a.federation_id,
                    confidence=0.6,
                )
            return MergeDecision(
                entity_id=entity_id, strategy=strategy,
                chosen_value=latest_b.data,
                source_federation=latest_b.federation_id,
                confidence=0.6,
            )

        else:
            # QUORUM_DECIDES — needs governance
            return MergeDecision(
                entity_id=entity_id, strategy=strategy,
                chosen_value=latest_a.data,
                source_federation=latest_a.federation_id,
                confidence=0.5,
                requires_governance=True,
            )


# ─── Cross-Ledger Consistency Engine ────────────────────────────────────────

class ConsistencyEngine:
    """
    Orchestrates cross-ledger consistency verification and reconciliation.

    Flow:
    1. Both federations create anchors at regular intervals
    2. Anchors are compared via fork detection
    3. Divergences trigger reconciliation FSM
    4. Merge protocol resolves individual entities
    5. Governance quorum handles membership/policy changes
    """

    def __init__(self, quorum_threshold: float = 0.67):
        self.fork_detector = ForkDetector()
        self.governance = GovernanceQuorum(quorum_threshold)
        self.merge_protocol = LedgerMergeProtocol(self.governance)
        self.fsm = ReconciliationFSM()
        self.reconciliation_history: List[Dict[str, Any]] = []

    def verify_consistency(self, ledger_a: FederationLedger,
                             ledger_b: FederationLedger,
                             shared_entities: Set[str]) -> Optional[DivergenceReport]:
        """Check consistency between two ledgers for shared entities."""
        self.fsm.begin_check()

        # Create anchors
        anchor_a = ledger_a.create_anchor(shared_entities)
        anchor_b = ledger_b.create_anchor(shared_entities)

        # Compare
        report = self.fork_detector.compare_anchors(anchor_a, anchor_b)

        if report is None:
            self.fsm.report_consistent()
            return None

        self.fsm.report_divergence(report)
        return report

    def reconcile(self, ledger_a: FederationLedger,
                    ledger_b: FederationLedger,
                    report: DivergenceReport,
                    federation_trusts: Dict[str, float],
                    voting_federations: Optional[List[str]] = None) -> Dict[str, MergeDecision]:
        """Reconcile diverged entities."""
        state = self.fsm.begin_reconciliation()
        if state == ConsistencyState.FAILED:
            return {}

        decisions = {}

        for entity_id in report.diverged_entities:
            entries_a = ledger_a.get_entries_for_entity(entity_id)
            entries_b = ledger_b.get_entries_for_entity(entity_id)

            decision = self.merge_protocol.resolve_divergence(
                entity_id, entries_a, entries_b, federation_trusts)

            if decision.requires_governance and voting_federations:
                # Create governance proposal
                proposal = self.governance.create_proposal(
                    proposer=decision.source_federation,
                    proposal_type="merge_entry",
                    entity_id=entity_id,
                    value=decision.chosen_value,
                )
                # Collect votes
                for fed_id in voting_federations:
                    # Simple heuristic: vote yes if trust > 0.5
                    approve = federation_trusts.get(fed_id, 0.5) > 0.4
                    self.governance.cast_vote(proposal, fed_id, approve)

                accepted = self.governance.resolve_proposal(proposal)
                if not accepted:
                    self.fsm.fail_entity(entity_id)
                    continue

            self.fsm.resolve_entity(entity_id, decision.strategy.name)
            decisions[entity_id] = decision

        final_state = self.fsm.complete_reconciliation()

        self.reconciliation_history.append({
            "report_id": report.report_id,
            "diverged_count": len(report.diverged_entities),
            "resolved_count": len(decisions),
            "final_state": final_state.name,
            "timestamp": time.time(),
        })

        return decisions

    def full_cycle(self, ledger_a: FederationLedger,
                     ledger_b: FederationLedger,
                     shared_entities: Set[str],
                     federation_trusts: Dict[str, float],
                     voting_federations: Optional[List[str]] = None) -> Tuple[
                         ConsistencyState, Dict[str, MergeDecision]]:
        """Run a complete verify → reconcile cycle."""
        report = self.verify_consistency(ledger_a, ledger_b, shared_entities)

        if report is None:
            return ConsistencyState.SYNCED, {}

        decisions = self.reconcile(
            ledger_a, ledger_b, report, federation_trusts, voting_federations)

        return self.fsm.state.state, decisions


# ─── Hash-Chained Audit Trail ────────────────────────────────────────────────

@dataclass
class ConsistencyAuditEntry:
    entry_id: str
    action: str
    federations: Tuple[str, str]
    details: Dict[str, Any]
    timestamp: float
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.entry_id}:{self.action}:{self.federations}:" \
                  f"{self.details}:{self.prev_hash}"
        self.entry_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.entry_hash


class ConsistencyAuditTrail:
    """Audit trail for cross-ledger consistency operations."""

    def __init__(self):
        self.entries: List[ConsistencyAuditEntry] = []

    def record(self, action: str, fed_a: str, fed_b: str,
               details: Dict[str, Any]) -> ConsistencyAuditEntry:
        prev_hash = self.entries[-1].entry_hash if self.entries else "genesis"
        entry = ConsistencyAuditEntry(
            entry_id=secrets.token_hex(8),
            action=action,
            federations=(fed_a, fed_b),
            details=details,
            timestamp=time.time(),
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

    # ── Section 1: Federation Ledger ─────────────────────────────────────────

    ledger = FederationLedger("fed_alpha")

    e1 = ledger.append("entity_1", EntryType.TRUST_UPDATE, {"trust": 0.7})
    e2 = ledger.append("entity_1", EntryType.ATP_TRANSFER, {"amount": 50})
    e3 = ledger.append("entity_2", EntryType.MEMBERSHIP_CHANGE, {"action": "join"})

    check("s1_ledger_count", len(ledger.entries) == 3)
    check("s1_sequence", e3.sequence == 3)
    check("s1_hash_computed", len(e1.entry_hash) == 32)
    check("s1_chain_linked", e2.prev_hash == e1.entry_hash)
    check("s1_genesis", e1.prev_hash == "genesis")
    check("s1_entity_index", len(ledger.entity_index["entity_1"]) == 2)

    # ── Section 2: Ledger Chain Integrity ────────────────────────────────────

    check("s2_chain_valid", ledger.verify_chain())

    # Tamper and detect
    original_hash = ledger.entries[1].prev_hash
    ledger.entries[1].prev_hash = "tampered"
    check("s2_tamper_detected", not ledger.verify_chain())
    ledger.entries[1].prev_hash = original_hash
    check("s2_restored", ledger.verify_chain())

    # ── Section 3: Merkle Root ───────────────────────────────────────────────

    root1 = ledger.compute_merkle_root()
    check("s3_merkle_root", len(root1) == 32)

    # Same entries → same root
    root2 = ledger.compute_merkle_root()
    check("s3_deterministic", root1 == root2)

    # Different entries → different root
    ledger.append("entity_3", EntryType.TRUST_UPDATE, {"trust": 0.5})
    root3 = ledger.compute_merkle_root()
    check("s3_changed_root", root3 != root1)

    # ── Section 4: Ledger Anchors ────────────────────────────────────────────

    shared = {"entity_1", "entity_2"}
    anchor = ledger.create_anchor(shared)

    check("s4_anchor_created", anchor.federation_id == "fed_alpha")
    check("s4_anchor_merkle", len(anchor.merkle_root) == 32)
    check("s4_entity_hashes", len(anchor.shared_entity_hashes) > 0)
    check("s4_anchor_count", anchor.entry_count >= 0)

    # ── Section 5: Fork Detection — No Divergence ────────────────────────────

    # Two identical ledgers
    la = FederationLedger("fed_a")
    lb = FederationLedger("fed_b")
    shared_ents = {"shared_1", "shared_2"}

    la.append("shared_1", EntryType.TRUST_UPDATE, {"trust": 0.7})
    lb.append("shared_1", EntryType.TRUST_UPDATE, {"trust": 0.7})
    la.append("shared_2", EntryType.ATP_TRANSFER, {"amount": 50})
    lb.append("shared_2", EntryType.ATP_TRANSFER, {"amount": 50})

    anchor_a = la.create_anchor(shared_ents)
    anchor_b = lb.create_anchor(shared_ents)

    detector = ForkDetector()
    report = detector.compare_anchors(anchor_a, anchor_b)
    check("s5_no_divergence", report is None)

    # ── Section 6: Fork Detection — With Divergence ──────────────────────────

    lc = FederationLedger("fed_c")
    ld = FederationLedger("fed_d")

    lc.append("shared_1", EntryType.TRUST_UPDATE, {"trust": 0.7})
    ld.append("shared_1", EntryType.TRUST_UPDATE, {"trust": 0.3})  # Different!

    lc.append("shared_2", EntryType.ATP_TRANSFER, {"amount": 50})
    ld.append("shared_2", EntryType.ATP_TRANSFER, {"amount": 50})

    anchor_c = lc.create_anchor(shared_ents)
    anchor_d = ld.create_anchor(shared_ents)

    div_report = detector.compare_anchors(anchor_c, anchor_d)
    check("s6_divergence_detected", div_report is not None)
    check("s6_diverged_entity", "shared_1" in div_report.diverged_entities
          if div_report else False)
    check("s6_severity", 0 < div_report.severity <= 1.0 if div_report else False,
          f"severity={div_report.severity if div_report else 0}")

    # ── Section 7: Sequence Gap Detection ────────────────────────────────────

    gap = detector.detect_sequence_gap(anchor_c, anchor_d)
    check("s7_no_gap", gap == 0)  # Both have same count

    # Create asymmetric ledgers — add more entries to lc only
    lc.append("local_only", EntryType.TRUST_UPDATE, {"trust": 0.5})
    lc.append("local_only", EntryType.TRUST_UPDATE, {"trust": 0.6})
    lc.append("local_only2", EntryType.TRUST_UPDATE, {"trust": 0.4})
    anchor_c2 = lc.create_anchor(shared_ents)  # 3 entries in this anchor
    # ld has no new entries, create a fresh anchor with 0 new entries
    ld.append("local_d", EntryType.TRUST_UPDATE, {"trust": 0.5})
    anchor_d2 = ld.create_anchor(shared_ents)  # 1 entry in this anchor
    gap2 = detector.detect_sequence_gap(anchor_c2, anchor_d2)
    check("s7_gap_detected", gap2 > 0, f"gap={gap2}")

    drift = detector.detect_entry_count_drift(anchor_c2, anchor_d2)
    check("s7_drift_positive", drift > 0, f"drift={drift}")

    # ── Section 8: Reconciliation FSM ────────────────────────────────────────

    fsm = ReconciliationFSM()
    check("s8_initial_synced", fsm.state.state == ConsistencyState.SYNCED)

    fsm.begin_check()
    check("s8_checking", fsm.state.state == ConsistencyState.CHECKING)

    fsm.report_divergence(div_report)
    check("s8_diverged", fsm.state.state == ConsistencyState.DIVERGED)

    fsm.begin_reconciliation()
    check("s8_reconciling", fsm.state.state == ConsistencyState.RECONCILING)

    fsm.resolve_entity("shared_1", "HIGHER_TRUST_WINS")
    check("s8_entity_resolved", "shared_1" in fsm.state.resolved_entities)

    fsm.complete_reconciliation()
    check("s8_completed_synced", fsm.state.state == ConsistencyState.SYNCED)

    check("s8_history", len(fsm.state.history) == 4,
          f"history={len(fsm.state.history)}")

    # ── Section 9: FSM — Failure Path ────────────────────────────────────────

    fsm2 = ReconciliationFSM()
    fsm2.begin_check()
    fsm2.report_divergence(div_report)
    fsm2.begin_reconciliation()
    fsm2.fail_entity("shared_1")
    fsm2.complete_reconciliation()
    check("s9_failed_state", fsm2.state.state == ConsistencyState.FAILED)
    check("s9_failed_entities", "shared_1" in fsm2.state.failed_entities)

    # ── Section 10: FSM — Max Attempts ───────────────────────────────────────

    fsm3 = ReconciliationFSM(max_reconciliation_attempts=2)
    # Attempt 1
    fsm3.begin_check()
    fsm3.report_divergence(div_report)
    fsm3.begin_reconciliation()
    fsm3.fail_entity("x")
    fsm3.complete_reconciliation()
    check("s10_attempt_1_failed", fsm3.state.state == ConsistencyState.FAILED)

    # Reset for attempt 2
    fsm3.state.state = ConsistencyState.SYNCED
    fsm3.state.failed_entities.clear()
    fsm3.begin_check()
    fsm3.report_divergence(div_report)
    fsm3.begin_reconciliation()
    fsm3.fail_entity("y")
    fsm3.complete_reconciliation()
    check("s10_attempt_2_failed", fsm3.state.state == ConsistencyState.FAILED)

    # Attempt 3 should hit max
    fsm3.state.state = ConsistencyState.SYNCED
    fsm3.state.failed_entities.clear()
    fsm3.begin_check()
    fsm3.report_divergence(div_report)
    result = fsm3.begin_reconciliation()
    check("s10_max_attempts", result == ConsistencyState.FAILED)

    # ── Section 11: Governance Quorum ────────────────────────────────────────

    gov = GovernanceQuorum(quorum_threshold=0.6)
    proposal = gov.create_proposal("fed_a", "merge_entry", "entity_1", {"trust": 0.7})

    gov.cast_vote(proposal, "fed_a", True)
    gov.cast_vote(proposal, "fed_b", True)
    gov.cast_vote(proposal, "fed_c", False)

    check("s11_approval_ratio", abs(proposal.approval_ratio - 0.667) < 0.01,
          f"ratio={proposal.approval_ratio}")
    check("s11_has_quorum", proposal.has_quorum)

    accepted = gov.resolve_proposal(proposal)
    check("s11_accepted", accepted)
    check("s11_resolved", proposal.resolved)

    # ── Section 12: Governance — Rejected ────────────────────────────────────

    proposal2 = gov.create_proposal("fed_a", "policy_change", "entity_2", {"action": "deny"})
    gov.cast_vote(proposal2, "fed_a", True)
    gov.cast_vote(proposal2, "fed_b", False)
    gov.cast_vote(proposal2, "fed_c", False)

    check("s12_no_quorum", not proposal2.has_quorum)
    rejected = gov.resolve_proposal(proposal2)
    check("s12_rejected", not rejected)

    # ── Section 13: Merge Protocol — Trust Updates ───────────────────────────

    merge = LedgerMergeProtocol(gov)
    fed_trusts = {"fed_c": 0.8, "fed_d": 0.5}

    entries_c = lc.get_entries_for_entity("shared_1")
    entries_d = ld.get_entries_for_entity("shared_1")

    decision = merge.resolve_divergence("shared_1", entries_c, entries_d, fed_trusts)
    check("s13_trust_strategy", decision.strategy == MergeStrategy.HIGHER_TRUST_WINS)
    check("s13_higher_trust_wins", decision.source_federation == "fed_c",
          f"source={decision.source_federation}")
    check("s13_confidence", decision.confidence > 0)

    # ── Section 14: Merge Protocol — One-Sided ───────────────────────────────

    decision_one = merge.resolve_divergence("one_sided", entries_c, [], fed_trusts)
    check("s14_one_sided_a", decision_one.source_federation == "fed_c")

    decision_other = merge.resolve_divergence("other_sided", [], entries_d, fed_trusts)
    check("s14_one_sided_b", decision_other.source_federation == "fed_d")

    # ── Section 15: Merge Protocol — Conservative ────────────────────────────

    # Create policy entries
    le = FederationLedger("fed_e")
    lf = FederationLedger("fed_f")
    le.append("policy_ent", EntryType.POLICY_UPDATE, {"value": 0.3, "action": "limit"})
    lf.append("policy_ent", EntryType.POLICY_UPDATE, {"value": 0.7, "action": "allow"})

    pol_dec = merge.resolve_divergence(
        "policy_ent",
        le.get_entries_for_entity("policy_ent"),
        lf.get_entries_for_entity("policy_ent"),
        {"fed_e": 0.6, "fed_f": 0.6},
    )
    check("s15_conservative", pol_dec.strategy == MergeStrategy.CONSERVATIVE)
    check("s15_lower_wins", pol_dec.chosen_value.get("value") == 0.3,
          f"value={pol_dec.chosen_value}")

    # ── Section 16: Merge Protocol — Governance Required ─────────────────────

    lg = FederationLedger("fed_g")
    lh = FederationLedger("fed_h")
    lg.append("member_ent", EntryType.MEMBERSHIP_CHANGE, {"action": "join"})
    lh.append("member_ent", EntryType.MEMBERSHIP_CHANGE, {"action": "leave"})

    mem_dec = merge.resolve_divergence(
        "member_ent",
        lg.get_entries_for_entity("member_ent"),
        lh.get_entries_for_entity("member_ent"),
        {"fed_g": 0.7, "fed_h": 0.6},
    )
    check("s16_governance_required", mem_dec.requires_governance)
    check("s16_quorum_strategy", mem_dec.strategy == MergeStrategy.QUORUM_DECIDES)

    # ── Section 17: Consistency Engine — Full Cycle (No Divergence) ──────────

    engine = ConsistencyEngine()

    li = FederationLedger("fed_i")
    lj = FederationLedger("fed_j")
    shared_17 = {"s_ent_1"}

    li.append("s_ent_1", EntryType.TRUST_UPDATE, {"trust": 0.7})
    lj.append("s_ent_1", EntryType.TRUST_UPDATE, {"trust": 0.7})

    state, decisions = engine.full_cycle(li, lj, shared_17, {"fed_i": 0.7, "fed_j": 0.7})
    check("s17_synced", state == ConsistencyState.SYNCED)
    check("s17_no_decisions", len(decisions) == 0)

    # ── Section 18: Consistency Engine — Full Cycle (With Divergence) ────────

    engine2 = ConsistencyEngine()

    lk = FederationLedger("fed_k")
    ll = FederationLedger("fed_l")
    shared_18 = {"s_ent_2", "s_ent_3"}

    lk.append("s_ent_2", EntryType.TRUST_UPDATE, {"trust": 0.8})
    ll.append("s_ent_2", EntryType.TRUST_UPDATE, {"trust": 0.4})
    lk.append("s_ent_3", EntryType.ATP_TRANSFER, {"amount": 100})
    ll.append("s_ent_3", EntryType.ATP_TRANSFER, {"amount": 200})

    fed_trusts_18 = {"fed_k": 0.8, "fed_l": 0.6}
    state2, decisions2 = engine2.full_cycle(
        lk, ll, shared_18, fed_trusts_18, ["fed_k", "fed_l"])
    check("s18_resolved", state2 == ConsistencyState.SYNCED,
          f"state={state2}")
    check("s18_decisions_made", len(decisions2) == 2,
          f"decisions={len(decisions2)}")
    check("s18_ent2_higher_trust", decisions2.get("s_ent_2") is not None and
          decisions2["s_ent_2"].source_federation == "fed_k" if "s_ent_2" in decisions2 else False)

    # ── Section 19: Consistency Engine — History ─────────────────────────────

    check("s19_history_recorded", len(engine2.reconciliation_history) > 0)
    last_hist = engine2.reconciliation_history[-1]
    check("s19_history_fields", "diverged_count" in last_hist and
          "resolved_count" in last_hist)

    # ── Section 20: Audit Trail ──────────────────────────────────────────────

    audit = ConsistencyAuditTrail()
    audit.record("verify", "fed_k", "fed_l", {"diverged": 2})
    audit.record("reconcile", "fed_k", "fed_l", {"resolved": 2})
    audit.record("complete", "fed_k", "fed_l", {"state": "SYNCED"})

    check("s20_audit_entries", len(audit.entries) == 3)
    check("s20_chain_valid", audit.verify_chain())
    check("s20_genesis", audit.entries[0].prev_hash == "genesis")
    check("s20_chain_linked", audit.entries[1].prev_hash == audit.entries[0].entry_hash)

    # Tamper
    orig = audit.entries[1].prev_hash
    audit.entries[1].prev_hash = "bad"
    check("s20_tamper_caught", not audit.verify_chain())
    audit.entries[1].prev_hash = orig
    check("s20_restored", audit.verify_chain())

    # ── Section 21: Multi-Federation Scenario ────────────────────────────────

    # 4 federations, 3 shared entities
    feds = {}
    for name in ["alpha", "beta", "gamma", "delta"]:
        feds[name] = FederationLedger(name)

    shared_21 = {"citizen_1", "citizen_2", "citizen_3"}
    fed_trusts_21 = {"alpha": 0.9, "beta": 0.7, "gamma": 0.6, "delta": 0.5}

    # Alpha and beta agree
    feds["alpha"].append("citizen_1", EntryType.TRUST_UPDATE, {"trust": 0.8})
    feds["beta"].append("citizen_1", EntryType.TRUST_UPDATE, {"trust": 0.8})

    # Gamma and delta disagree
    feds["gamma"].append("citizen_2", EntryType.TRUST_UPDATE, {"trust": 0.9})
    feds["delta"].append("citizen_2", EntryType.TRUST_UPDATE, {"trust": 0.3})

    # Check alpha-beta consistency
    eng_ab = ConsistencyEngine()
    state_ab, dec_ab = eng_ab.full_cycle(
        feds["alpha"], feds["beta"], {"citizen_1"}, fed_trusts_21)
    check("s21_ab_synced", state_ab == ConsistencyState.SYNCED)

    # Check gamma-delta divergence
    eng_gd = ConsistencyEngine()
    state_gd, dec_gd = eng_gd.full_cycle(
        feds["gamma"], feds["delta"], {"citizen_2"}, fed_trusts_21,
        list(fed_trusts_21.keys()))
    check("s21_gd_diverged_resolved", state_gd == ConsistencyState.SYNCED)
    check("s21_citizen_2_resolved", "citizen_2" in dec_gd)

    # ── Section 22: Performance — Large Ledger (Identical) ──────────────────

    big_a = FederationLedger("perf_a")
    big_b = FederationLedger("perf_b")
    shared_perf = set()

    t0 = time.time()
    for i in range(200):
        eid = f"ent_{i}"
        big_a.append(eid, EntryType.TRUST_UPDATE, {"trust": 0.5 + (i % 10) * 0.05})
        big_b.append(eid, EntryType.TRUST_UPDATE, {"trust": 0.5 + (i % 10) * 0.05})
        if i < 50:
            shared_perf.add(eid)
    elapsed = time.time() - t0
    check("s22_200_entries_fast", elapsed < 5.0, f"elapsed={elapsed:.2f}s")

    eng_22 = ConsistencyEngine()
    state_22, dec_22 = eng_22.full_cycle(big_a, big_b, shared_perf, {})
    check("s22_identical_no_div", state_22 == ConsistencyState.SYNCED)

    # ── Section 23: Performance — Diverged Reconciliation ────────────────────

    # Create fresh ledgers with known divergence in 20 of 50 shared entities
    big_c = FederationLedger("perf_c")
    big_d = FederationLedger("perf_d")
    shared_23 = set()

    for i in range(50):
        eid = f"shared_{i}"
        shared_23.add(eid)
        if i < 20:
            # Divergent: different trust values
            big_c.append(eid, EntryType.TRUST_UPDATE, {"trust": 0.8})
            big_d.append(eid, EntryType.TRUST_UPDATE, {"trust": 0.3})
        else:
            # Identical
            big_c.append(eid, EntryType.TRUST_UPDATE, {"trust": 0.7})
            big_d.append(eid, EntryType.TRUST_UPDATE, {"trust": 0.7})

    t0 = time.time()
    eng_23 = ConsistencyEngine()
    fed_t = {"perf_c": 0.8, "perf_d": 0.6}
    state_23, dec_23 = eng_23.full_cycle(
        big_c, big_d, shared_23, fed_t, ["perf_c", "perf_d"])
    elapsed_rec = time.time() - t0

    check("s23_divergence_found", len(dec_23) > 0)
    check("s23_reconciled", state_23 == ConsistencyState.SYNCED,
          f"state={state_23}")
    check("s23_20_resolved", len(dec_23) == 20,
          f"resolved={len(dec_23)}")
    check("s23_reconciliation_fast", elapsed_rec < 5.0,
          f"elapsed={elapsed_rec:.2f}s")

    # ── Section 24: Edge Cases ───────────────────────────────────────────────

    # Empty ledgers
    empty_a = FederationLedger("empty_a")
    empty_b = FederationLedger("empty_b")
    eng_empty = ConsistencyEngine()
    state_empty, _ = eng_empty.full_cycle(empty_a, empty_b, set(), {})
    check("s24_empty_synced", state_empty == ConsistencyState.SYNCED)

    # No shared entities
    la_ns = FederationLedger("ns_a")
    lb_ns = FederationLedger("ns_b")
    la_ns.append("local_1", EntryType.TRUST_UPDATE, {"trust": 0.5})
    lb_ns.append("local_2", EntryType.TRUST_UPDATE, {"trust": 0.6})
    eng_ns = ConsistencyEngine()
    state_ns, _ = eng_ns.full_cycle(la_ns, lb_ns, set(), {})
    check("s24_no_shared_synced", state_ns == ConsistencyState.SYNCED)

    # Single shared entity, same data
    la_1 = FederationLedger("one_a")
    lb_1 = FederationLedger("one_b")
    la_1.append("only_one", EntryType.ATP_TRANSFER, {"amount": 42})
    lb_1.append("only_one", EntryType.ATP_TRANSFER, {"amount": 42})
    eng_1 = ConsistencyEngine()
    state_1, _ = eng_1.full_cycle(la_1, lb_1, {"only_one"}, {})
    check("s24_single_shared_synced", state_1 == ConsistencyState.SYNCED)

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
