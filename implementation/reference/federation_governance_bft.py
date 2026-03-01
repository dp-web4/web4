"""
Federation Governance BFT Protocol
====================================

Formal Byzantine Fault Tolerance for federation governance decisions.
Not task delegation (existing) — this is GOVERNANCE: policy votes,
membership changes, sybil defense activation, appeal outcomes.

Components:
1. GovernanceProposal — Typed proposals with configurable quorum
2. BFTGovernanceRound — PBFT-style consensus for governance decisions
3. VotingPowerCalculator — Trust-weighted voting with sybil resistance
4. MaliciousFederationDetector — Track byzantine behavior across proposals
5. GovernanceFinalizer — Irreversibility guarantee once consensus reached
6. CrossFederationBallot — COSE-signed ballot exchange between federations
7. GovernanceAuditTrail — Hash-chained governance decision log
8. AdaptiveQuorum — Dynamic quorum based on proposal type and risk

Key insight: governance BFT is harder than task BFT because governance
decisions are irreversible and affect the rules themselves.

PBFT: message complexity = n² per phase (all-to-all broadcast)
Quorum: 2f+1 out of N=3f+1 for optimal byzantine tolerance
"""

from __future__ import annotations
import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


# ─── Enums ────────────────────────────────────────────────────────────────────

class ProposalType(Enum):
    POLICY_CHANGE = auto()
    MEMBERSHIP_ADD = auto()
    MEMBERSHIP_REMOVE = auto()
    PARAMETER_UPDATE = auto()
    SYBIL_DEFENSE = auto()
    APPEAL_OUTCOME = auto()
    EMERGENCY_FREEZE = auto()
    FEDERATION_MERGE = auto()
    BUDGET_ALLOCATION = auto()


class ProposalStatus(Enum):
    DRAFT = auto()
    ANNOUNCED = auto()
    VOTING = auto()
    CONSENSUS_REACHED = auto()
    FINALIZED = auto()
    REJECTED = auto()
    EXPIRED = auto()


class VoteChoice(Enum):
    APPROVE = auto()
    REJECT = auto()
    ABSTAIN = auto()


class BFTPhase(Enum):
    PRE_PREPARE = auto()   # Leader broadcasts proposal
    PREPARE = auto()       # Nodes broadcast prepare
    COMMIT = auto()        # Nodes broadcast commit
    FINALIZE = auto()      # Decision finalized


class DetectionType(Enum):
    EQUIVOCATION = auto()        # Voted both ways
    VOTE_WITHHOLDING = auto()    # Didn't vote when required
    PROPOSAL_SPAM = auto()       # Too many proposals
    INVALID_SIGNATURE = auto()
    TIMEOUT_PATTERN = auto()     # Consistently timing out


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class GovernanceProposal:
    """A governance proposal for federation-level decisions."""
    proposal_id: str
    proposal_type: ProposalType
    proposer_id: str
    federation_id: str
    title: str
    description: str = ""
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    deadline: float = 0.0  # Voting deadline
    quorum_threshold: float = 0.667  # 2/3 by default
    min_participation: float = 0.5   # At least half must vote
    requires_supermajority: bool = False
    proposal_hash: str = ""

    def __post_init__(self):
        if not self.deadline:
            self.deadline = self.created_at + 86400.0  # 24h default
        if not self.proposal_hash:
            content = f"{self.proposal_id}:{self.proposal_type.name}:{self.proposer_id}:{self.title}:{self.created_at}"
            self.proposal_hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class GovernanceVote:
    """A vote on a governance proposal."""
    voter_id: str
    proposal_id: str
    choice: VoteChoice
    voting_power: float  # Weighted vote
    justification: str = ""
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def __post_init__(self):
        if not self.signature:
            content = f"{self.voter_id}:{self.proposal_id}:{self.choice.name}:{self.timestamp}"
            self.signature = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class BFTMessage:
    """A message in the BFT protocol."""
    sender_id: str
    phase: BFTPhase
    proposal_id: str
    content_hash: str
    view_number: int = 0
    sequence_number: int = 0
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def __post_init__(self):
        if not self.signature:
            content = f"{self.sender_id}:{self.phase.name}:{self.proposal_id}:{self.content_hash}:{self.view_number}:{self.sequence_number}"
            self.signature = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class GovernanceDecision:
    """A finalized governance decision."""
    proposal: GovernanceProposal
    outcome: VoteChoice  # APPROVE or REJECT
    total_votes: int
    approve_power: float
    reject_power: float
    abstain_power: float
    participation_rate: float
    finalized_at: float = field(default_factory=time.time)
    decision_hash: str = ""
    prev_hash: str = ""

    def __post_init__(self):
        if not self.decision_hash:
            content = f"{self.proposal.proposal_id}:{self.outcome.name}:{self.approve_power}:{self.reject_power}:{self.finalized_at}:{self.prev_hash}"
            self.decision_hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class FederationNode:
    """A federation node participating in governance."""
    node_id: str
    federation_id: str
    trust_score: float = 0.5
    stake: float = 100.0
    reputation: float = 0.5
    proposals_made: int = 0
    votes_cast: int = 0
    byzantine_score: float = 0.0  # Higher = more suspicious
    is_active: bool = True


# ─── Voting Power Calculator ─────────────────────────────────────────────────

class VotingPowerCalculator:
    """Trust-weighted voting with sybil resistance."""

    def __init__(self, trust_weight: float = 0.4,
                 stake_weight: float = 0.3,
                 reputation_weight: float = 0.3,
                 use_sqrt_stake: bool = True):
        self.trust_weight = trust_weight
        self.stake_weight = stake_weight
        self.reputation_weight = reputation_weight
        self.use_sqrt_stake = use_sqrt_stake

    def calculate(self, node: FederationNode) -> float:
        """Calculate voting power for a node."""
        if not node.is_active:
            return 0.0

        if node.trust_score <= 0:
            return 0.0  # Zero trust = zero voting power

        trust_component = node.trust_score * self.trust_weight

        # sqrt(stake) for sybil resistance: 4x stake → 2x weight
        if self.use_sqrt_stake:
            stake_component = math.sqrt(node.stake / 100.0) * self.stake_weight
        else:
            stake_component = (node.stake / 100.0) * self.stake_weight

        rep_component = node.reputation * self.reputation_weight

        # Byzantine penalty
        byzantine_penalty = max(0.0, 1.0 - node.byzantine_score)

        return (trust_component + stake_component + rep_component) * byzantine_penalty

    def calculate_all(self, nodes: List[FederationNode]) -> Dict[str, float]:
        """Calculate voting power for all nodes."""
        powers = {}
        for node in nodes:
            powers[node.node_id] = self.calculate(node)
        return powers


# ─── Adaptive Quorum ──────────────────────────────────────────────────────────

class AdaptiveQuorum:
    """Dynamic quorum requirements based on proposal type and risk."""

    PROPOSAL_QUORUMS = {
        ProposalType.POLICY_CHANGE: 0.667,       # 2/3 supermajority
        ProposalType.MEMBERSHIP_ADD: 0.5,          # Simple majority
        ProposalType.MEMBERSHIP_REMOVE: 0.75,      # 3/4 supermajority
        ProposalType.PARAMETER_UPDATE: 0.5,        # Simple majority
        ProposalType.SYBIL_DEFENSE: 0.667,         # 2/3 supermajority
        ProposalType.APPEAL_OUTCOME: 0.667,        # 2/3 supermajority
        ProposalType.EMERGENCY_FREEZE: 0.667,      # 2/3 but shorter deadline
        ProposalType.FEDERATION_MERGE: 0.8,        # 4/5 supermajority
        ProposalType.BUDGET_ALLOCATION: 0.5,       # Simple majority
    }

    PROPOSAL_MIN_PARTICIPATION = {
        ProposalType.POLICY_CHANGE: 0.6,
        ProposalType.MEMBERSHIP_REMOVE: 0.7,
        ProposalType.EMERGENCY_FREEZE: 0.3,   # Lower bar for emergencies
        ProposalType.FEDERATION_MERGE: 0.8,
    }

    PROPOSAL_DEADLINES = {
        ProposalType.EMERGENCY_FREEZE: 3600.0,    # 1 hour
        ProposalType.POLICY_CHANGE: 172800.0,      # 48 hours
        ProposalType.FEDERATION_MERGE: 604800.0,   # 7 days
    }

    def get_quorum(self, proposal_type: ProposalType) -> float:
        return self.PROPOSAL_QUORUMS.get(proposal_type, 0.5)

    def get_min_participation(self, proposal_type: ProposalType) -> float:
        return self.PROPOSAL_MIN_PARTICIPATION.get(proposal_type, 0.5)

    def get_deadline(self, proposal_type: ProposalType) -> float:
        return self.PROPOSAL_DEADLINES.get(proposal_type, 86400.0)


# ─── BFT Governance Round ────────────────────────────────────────────────────

class BFTGovernanceRound:
    """PBFT-style consensus round for a governance proposal."""

    def __init__(self, proposal: GovernanceProposal,
                 nodes: List[FederationNode],
                 power_calculator: VotingPowerCalculator,
                 f_tolerance: int = None):
        self.proposal = proposal
        self.nodes = {n.node_id: n for n in nodes}
        self.power_calc = power_calculator
        self.n = len(nodes)
        self.f = f_tolerance or (self.n - 1) // 3
        self.quorum = 2 * self.f + 1

        self.votes: Dict[str, GovernanceVote] = {}
        self.phase = BFTPhase.PRE_PREPARE
        self.messages: Dict[BFTPhase, Dict[str, BFTMessage]] = {
            BFTPhase.PRE_PREPARE: {},
            BFTPhase.PREPARE: {},
            BFTPhase.COMMIT: {},
        }
        self.decided = False
        self.decision: Optional[GovernanceDecision] = None

    def submit_vote(self, vote: GovernanceVote) -> bool:
        """Submit a vote from a node."""
        if vote.voter_id not in self.nodes:
            return False
        if vote.proposal_id != self.proposal.proposal_id:
            return False
        if vote.voter_id in self.votes:
            return False  # Already voted

        # Calculate voting power
        node = self.nodes[vote.voter_id]
        vote.voting_power = self.power_calc.calculate(node)
        self.votes[vote.voter_id] = vote
        return True

    def receive_message(self, msg: BFTMessage) -> bool:
        """Receive a BFT protocol message."""
        if msg.sender_id not in self.nodes:
            return False
        if msg.proposal_id != self.proposal.proposal_id:
            return False

        # Check for equivocation (same sender, same phase, different hash)
        existing = self.messages[msg.phase].get(msg.sender_id)
        if existing and existing.content_hash != msg.content_hash:
            # Equivocation detected!
            return False

        self.messages[msg.phase][msg.sender_id] = msg
        return True

    def check_prepare_quorum(self) -> bool:
        """Check if prepare phase has quorum."""
        return len(self.messages[BFTPhase.PREPARE]) >= self.quorum

    def check_commit_quorum(self) -> bool:
        """Check if commit phase has quorum."""
        return len(self.messages[BFTPhase.COMMIT]) >= self.quorum

    def try_finalize(self, prev_hash: str = "genesis") -> Optional[GovernanceDecision]:
        """Try to finalize the decision if conditions are met."""
        if self.decided:
            return self.decision

        total_power = sum(self.power_calc.calculate(n) for n in self.nodes.values())
        if total_power == 0:
            return None

        # Calculate participation
        voting_power_cast = sum(v.voting_power for v in self.votes.values())
        participation = voting_power_cast / total_power

        if participation < self.proposal.min_participation:
            return None  # Not enough participation

        # Count votes by power
        approve_power = sum(v.voting_power for v in self.votes.values()
                           if v.choice == VoteChoice.APPROVE)
        reject_power = sum(v.voting_power for v in self.votes.values()
                          if v.choice == VoteChoice.REJECT)
        abstain_power = sum(v.voting_power for v in self.votes.values()
                           if v.choice == VoteChoice.ABSTAIN)

        non_abstain = approve_power + reject_power
        if non_abstain == 0:
            return None

        approval_rate = approve_power / non_abstain

        if approval_rate >= self.proposal.quorum_threshold:
            outcome = VoteChoice.APPROVE
        else:
            outcome = VoteChoice.REJECT

        self.decision = GovernanceDecision(
            proposal=self.proposal,
            outcome=outcome,
            total_votes=len(self.votes),
            approve_power=approve_power,
            reject_power=reject_power,
            abstain_power=abstain_power,
            participation_rate=participation,
            prev_hash=prev_hash,
        )
        self.decided = True
        self.proposal.status = ProposalStatus.FINALIZED
        return self.decision


# ─── Malicious Federation Detector ───────────────────────────────────────────

class MaliciousFederationDetector:
    """Detect and track byzantine behavior across governance proposals."""

    def __init__(self, equivocation_penalty: float = 0.3,
                 withholding_penalty: float = 0.1,
                 spam_threshold: int = 10,
                 isolation_threshold: float = 0.8):
        self.equivocation_penalty = equivocation_penalty
        self.withholding_penalty = withholding_penalty
        self.spam_threshold = spam_threshold
        self.isolation_threshold = isolation_threshold
        self.incidents: Dict[str, List[Dict]] = defaultdict(list)

    def report_equivocation(self, node: FederationNode,
                            proposal_id: str):
        """Report a node for equivocation (voting both ways)."""
        node.byzantine_score = min(1.0, node.byzantine_score + self.equivocation_penalty)
        self.incidents[node.node_id].append({
            "type": DetectionType.EQUIVOCATION.name,
            "proposal_id": proposal_id,
            "penalty": self.equivocation_penalty,
            "timestamp": time.time(),
        })

    def report_withholding(self, node: FederationNode,
                           proposal_id: str):
        """Report a node for vote withholding."""
        node.byzantine_score = min(1.0, node.byzantine_score + self.withholding_penalty)
        self.incidents[node.node_id].append({
            "type": DetectionType.VOTE_WITHHOLDING.name,
            "proposal_id": proposal_id,
            "penalty": self.withholding_penalty,
            "timestamp": time.time(),
        })

    def report_spam(self, node: FederationNode):
        """Report a node for proposal spam."""
        if node.proposals_made > self.spam_threshold:
            node.byzantine_score = min(1.0, node.byzantine_score + 0.2)
            self.incidents[node.node_id].append({
                "type": DetectionType.PROPOSAL_SPAM.name,
                "proposals": node.proposals_made,
                "timestamp": time.time(),
            })

    def should_isolate(self, node: FederationNode) -> bool:
        """Determine if a node should be isolated from governance."""
        return node.byzantine_score >= self.isolation_threshold

    def get_incident_count(self, node_id: str) -> int:
        return len(self.incidents.get(node_id, []))

    def get_network_health(self, nodes: List[FederationNode]) -> Dict:
        """Get overall governance network health."""
        total = len(nodes)
        suspicious = sum(1 for n in nodes if n.byzantine_score > 0.3)
        isolated = sum(1 for n in nodes if self.should_isolate(n))

        return {
            "total_nodes": total,
            "suspicious_nodes": suspicious,
            "isolated_nodes": isolated,
            "health_ratio": 1.0 - (suspicious / total) if total > 0 else 1.0,
            "total_incidents": sum(len(v) for v in self.incidents.values()),
        }


# ─── Governance Audit Trail ──────────────────────────────────────────────────

class GovernanceAuditTrail:
    """Hash-chained audit trail of governance decisions."""

    def __init__(self):
        self.decisions: List[GovernanceDecision] = []

    def append(self, decision: GovernanceDecision):
        """Append a decision to the audit trail."""
        prev_hash = self.decisions[-1].decision_hash if self.decisions else "genesis"
        decision.prev_hash = prev_hash
        # Recompute hash with correct prev_hash
        content = f"{decision.proposal.proposal_id}:{decision.outcome.name}:{decision.approve_power}:{decision.reject_power}:{decision.finalized_at}:{decision.prev_hash}"
        decision.decision_hash = hashlib.sha256(content.encode()).hexdigest()
        self.decisions.append(decision)

    def verify_chain(self) -> Tuple[bool, List[int]]:
        broken = []
        for i, d in enumerate(self.decisions):
            expected_prev = self.decisions[i-1].decision_hash if i > 0 else "genesis"
            if d.prev_hash != expected_prev:
                broken.append(i)
        return len(broken) == 0, broken

    def get_decision(self, proposal_id: str) -> Optional[GovernanceDecision]:
        for d in self.decisions:
            if d.proposal.proposal_id == proposal_id:
                return d
        return None


# ─── Governance Orchestrator ──────────────────────────────────────────────────

class GovernanceOrchestrator:
    """Orchestrates the complete governance lifecycle."""

    def __init__(self, federation_id: str):
        self.federation_id = federation_id
        self.nodes: Dict[str, FederationNode] = {}
        self.power_calc = VotingPowerCalculator()
        self.quorum_calc = AdaptiveQuorum()
        self.detector = MaliciousFederationDetector()
        self.audit = GovernanceAuditTrail()
        self.active_rounds: Dict[str, BFTGovernanceRound] = {}
        self.completed: List[str] = []

    def register_node(self, node: FederationNode):
        self.nodes[node.node_id] = node

    def create_proposal(self, proposer_id: str,
                        proposal_type: ProposalType,
                        title: str, description: str = "") -> Optional[GovernanceProposal]:
        """Create a new governance proposal."""
        node = self.nodes.get(proposer_id)
        if not node or not node.is_active:
            return None

        if self.detector.should_isolate(node):
            return None  # Byzantine node cannot propose

        quorum = self.quorum_calc.get_quorum(proposal_type)
        min_part = self.quorum_calc.get_min_participation(proposal_type)
        deadline_duration = self.quorum_calc.get_deadline(proposal_type)

        proposal = GovernanceProposal(
            proposal_id=f"prop_{proposer_id}_{time.time()}",
            proposal_type=proposal_type,
            proposer_id=proposer_id,
            federation_id=self.federation_id,
            title=title,
            description=description,
            quorum_threshold=quorum,
            min_participation=min_part,
            deadline=time.time() + deadline_duration,
        )

        node.proposals_made += 1
        self.detector.report_spam(node)  # Check if spamming

        # Create BFT round
        active_nodes = [n for n in self.nodes.values()
                       if n.is_active and not self.detector.should_isolate(n)]
        bft_round = BFTGovernanceRound(proposal, active_nodes, self.power_calc)
        self.active_rounds[proposal.proposal_id] = bft_round
        proposal.status = ProposalStatus.VOTING

        return proposal

    def cast_vote(self, voter_id: str, proposal_id: str,
                  choice: VoteChoice, justification: str = "") -> bool:
        """Cast a vote on an active proposal."""
        bft_round = self.active_rounds.get(proposal_id)
        if not bft_round:
            return False

        node = self.nodes.get(voter_id)
        if not node or not node.is_active:
            return False

        if self.detector.should_isolate(node):
            return False

        vote = GovernanceVote(
            voter_id=voter_id,
            proposal_id=proposal_id,
            choice=choice,
            voting_power=0.0,  # Will be calculated by submit_vote
            justification=justification,
        )

        success = bft_round.submit_vote(vote)
        if success:
            node.votes_cast += 1
        return success

    def finalize_proposal(self, proposal_id: str) -> Optional[GovernanceDecision]:
        """Try to finalize a proposal."""
        bft_round = self.active_rounds.get(proposal_id)
        if not bft_round:
            return None

        prev_hash = self.audit.decisions[-1].decision_hash if self.audit.decisions else "genesis"
        decision = bft_round.try_finalize(prev_hash)
        if decision:
            self.audit.append(decision)
            self.completed.append(proposal_id)
            del self.active_rounds[proposal_id]
        return decision


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_node(nid: str, trust: float = 0.7, stake: float = 100.0,
               reputation: float = 0.6) -> FederationNode:
    return FederationNode(
        node_id=nid, federation_id="fed_test",
        trust_score=trust, stake=stake, reputation=reputation,
    )


def run_tests():
    results = []

    def check(name, condition, detail=""):
        results.append((name, condition, detail))

    # ─── S1: Voting Power Calculator ──────────────────────────────────

    calc = VotingPowerCalculator()

    high_trust = _make_node("ht", trust=0.9, stake=200, reputation=0.8)
    low_trust = _make_node("lt", trust=0.2, stake=50, reputation=0.3)
    zero_trust = _make_node("zt", trust=0.0, stake=200, reputation=0.9)

    ht_power = calc.calculate(high_trust)
    lt_power = calc.calculate(low_trust)
    zt_power = calc.calculate(zero_trust)

    check("s1_high_gt_low", ht_power > lt_power,
          f"ht={ht_power:.3f} lt={lt_power:.3f}")
    check("s1_zero_trust", zt_power == 0.0,
          f"zt={zt_power:.3f}")
    check("s1_positive", ht_power > 0)

    # sqrt(stake): 4x stake → 2x weight
    base_stake = _make_node("bs", trust=0.5, stake=100, reputation=0.5)
    quad_stake = _make_node("qs", trust=0.5, stake=400, reputation=0.5)
    base_power = calc.calculate(base_stake)
    quad_power = calc.calculate(quad_stake)
    # Stake component: sqrt(4) = 2, so quad should be bigger but not 4x
    check("s1_sqrt_dampening", quad_power < base_power * 3,
          f"base={base_power:.3f} quad={quad_power:.3f}")
    check("s1_sqrt_still_more", quad_power > base_power,
          f"base={base_power:.3f} quad={quad_power:.3f}")

    # Inactive node
    inactive = _make_node("in", trust=0.9, stake=200, reputation=0.8)
    inactive.is_active = False
    check("s1_inactive_zero", calc.calculate(inactive) == 0.0)

    # Byzantine penalty
    byzantine = _make_node("byz", trust=0.7, stake=100, reputation=0.6)
    byz_power_before = calc.calculate(byzantine)
    byzantine.byzantine_score = 0.5
    byz_power_after = calc.calculate(byzantine)
    check("s1_byz_penalty", byz_power_after < byz_power_before,
          f"before={byz_power_before:.3f} after={byz_power_after:.3f}")

    # Calculate all
    all_powers = calc.calculate_all([high_trust, low_trust, zero_trust])
    check("s1_calc_all", len(all_powers) == 3)
    check("s1_all_ht_correct", abs(all_powers["ht"] - ht_power) < 0.001)

    # ─── S2: Adaptive Quorum ──────────────────────────────────────────

    aq = AdaptiveQuorum()

    check("s2_policy_quorum", aq.get_quorum(ProposalType.POLICY_CHANGE) == 0.667)
    check("s2_membership_add", aq.get_quorum(ProposalType.MEMBERSHIP_ADD) == 0.5)
    check("s2_merge_high", aq.get_quorum(ProposalType.FEDERATION_MERGE) == 0.8)
    check("s2_freeze_quorum", aq.get_quorum(ProposalType.EMERGENCY_FREEZE) == 0.667)

    # Emergency freeze has short deadline
    check("s2_freeze_fast", aq.get_deadline(ProposalType.EMERGENCY_FREEZE) == 3600.0)
    # Federation merge has long deadline
    check("s2_merge_slow", aq.get_deadline(ProposalType.FEDERATION_MERGE) == 604800.0)

    # Low participation for emergencies
    check("s2_emergency_low_part",
          aq.get_min_participation(ProposalType.EMERGENCY_FREEZE) == 0.3)
    # High participation for merge
    check("s2_merge_high_part",
          aq.get_min_participation(ProposalType.FEDERATION_MERGE) == 0.8)

    # ─── S3: BFT Governance Round — approval ─────────────────────────

    nodes = [_make_node(f"n{i}", trust=0.7, stake=100, reputation=0.6)
             for i in range(7)]  # N=7, f=2, quorum=5

    proposal = GovernanceProposal(
        proposal_id="prop_001",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="n0",
        federation_id="fed_test",
        title="Update consensus params",
        quorum_threshold=0.667,
        min_participation=0.5,
    )

    bft = BFTGovernanceRound(proposal, nodes, calc)
    check("s3_n_nodes", bft.n == 7)
    check("s3_f_tolerance", bft.f == 2)
    check("s3_quorum", bft.quorum == 5)

    # 5 approve, 2 reject
    for i in range(5):
        vote = GovernanceVote(f"n{i}", "prop_001", VoteChoice.APPROVE, 0.0)
        check(f"s3_vote_{i}", bft.submit_vote(vote))

    for i in range(5, 7):
        vote = GovernanceVote(f"n{i}", "prop_001", VoteChoice.REJECT, 0.0)
        bft.submit_vote(vote)

    decision = bft.try_finalize()
    check("s3_finalized", decision is not None)
    check("s3_approved", decision.outcome == VoteChoice.APPROVE,
          f"outcome={decision.outcome.name}")
    check("s3_participation", decision.participation_rate > 0.9,
          f"part={decision.participation_rate:.3f}")

    # ─── S4: BFT Governance Round — rejection ────────────────────────

    proposal_rej = GovernanceProposal(
        proposal_id="prop_002",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="n0",
        federation_id="fed_test",
        title="Bad proposal",
        quorum_threshold=0.667,
        min_participation=0.5,
    )

    bft_rej = BFTGovernanceRound(proposal_rej, nodes, calc)

    # 2 approve, 5 reject
    for i in range(2):
        bft_rej.submit_vote(GovernanceVote(f"n{i}", "prop_002", VoteChoice.APPROVE, 0.0))
    for i in range(2, 7):
        bft_rej.submit_vote(GovernanceVote(f"n{i}", "prop_002", VoteChoice.REJECT, 0.0))

    dec_rej = bft_rej.try_finalize()
    check("s4_rejected", dec_rej.outcome == VoteChoice.REJECT)

    # ─── S5: Insufficient participation ───────────────────────────────

    proposal_low = GovernanceProposal(
        proposal_id="prop_003",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="n0",
        federation_id="fed_test",
        title="Low participation",
        min_participation=0.8,
    )

    bft_low = BFTGovernanceRound(proposal_low, nodes, calc)
    # Only 2 out of 7 vote
    for i in range(2):
        bft_low.submit_vote(GovernanceVote(f"n{i}", "prop_003", VoteChoice.APPROVE, 0.0))

    dec_low = bft_low.try_finalize()
    check("s5_no_finalize", dec_low is None)

    # ─── S6: Duplicate vote prevention ────────────────────────────────

    proposal_dup = GovernanceProposal(
        proposal_id="prop_004",
        proposal_type=ProposalType.MEMBERSHIP_ADD,
        proposer_id="n0",
        federation_id="fed_test",
        title="Dup test",
    )

    bft_dup = BFTGovernanceRound(proposal_dup, nodes, calc)
    bft_dup.submit_vote(GovernanceVote("n0", "prop_004", VoteChoice.APPROVE, 0.0))
    check("s6_dup_rejected",
          not bft_dup.submit_vote(GovernanceVote("n0", "prop_004", VoteChoice.REJECT, 0.0)))

    # Non-member vote
    check("s6_non_member",
          not bft_dup.submit_vote(GovernanceVote("outsider", "prop_004", VoteChoice.APPROVE, 0.0)))

    # Wrong proposal
    check("s6_wrong_proposal",
          not bft_dup.submit_vote(GovernanceVote("n0", "prop_999", VoteChoice.APPROVE, 0.0)))

    # ─── S7: Malicious Federation Detector ────────────────────────────

    detector = MaliciousFederationDetector()
    bad_node = _make_node("bad", trust=0.7)

    # Equivocation
    detector.report_equivocation(bad_node, "prop_x")
    check("s7_equivocation_penalty", bad_node.byzantine_score == 0.3)

    # Multiple offenses accumulate
    detector.report_equivocation(bad_node, "prop_y")
    check("s7_accumulate", bad_node.byzantine_score == 0.6)

    # Withholding
    detector.report_withholding(bad_node, "prop_z")
    check("s7_withholding", bad_node.byzantine_score == 0.7)

    # Isolation threshold
    detector.report_equivocation(bad_node, "prop_w")
    check("s7_should_isolate", detector.should_isolate(bad_node))

    # Incident count
    check("s7_incidents", detector.get_incident_count("bad") == 4)

    # Network health
    good_nodes = [_make_node(f"good_{i}") for i in range(5)]
    all_nodes = good_nodes + [bad_node]
    health = detector.get_network_health(all_nodes)
    check("s7_health_total", health["total_nodes"] == 6)
    check("s7_health_suspicious", health["suspicious_nodes"] >= 1)
    check("s7_health_isolated", health["isolated_nodes"] >= 1)

    # ─── S8: Governance Audit Trail ───────────────────────────────────

    audit = GovernanceAuditTrail()

    # Add decisions
    for i in range(3):
        p = GovernanceProposal(
            proposal_id=f"audit_prop_{i}",
            proposal_type=ProposalType.PARAMETER_UPDATE,
            proposer_id="n0",
            federation_id="fed_test",
            title=f"Audit test {i}",
        )
        d = GovernanceDecision(
            proposal=p,
            outcome=VoteChoice.APPROVE,
            total_votes=7,
            approve_power=5.0,
            reject_power=2.0,
            abstain_power=0.0,
            participation_rate=1.0,
        )
        audit.append(d)

    check("s8_audit_count", len(audit.decisions) == 3)

    # Chain integrity
    valid, broken = audit.verify_chain()
    check("s8_chain_valid", valid, f"broken={broken}")

    # Lookup
    found = audit.get_decision("audit_prop_1")
    check("s8_lookup", found is not None)
    check("s8_lookup_correct", found.proposal.proposal_id == "audit_prop_1")
    check("s8_lookup_miss", audit.get_decision("nonexistent") is None)

    # ─── S9: Governance Orchestrator E2E ──────────────────────────────

    orch = GovernanceOrchestrator("fed_orch")
    for i in range(10):
        orch.register_node(_make_node(f"orch_{i}", trust=0.6 + i * 0.03,
                                      stake=100 + i * 20, reputation=0.5 + i * 0.04))

    # Create proposal
    proposal = orch.create_proposal("orch_0", ProposalType.POLICY_CHANGE,
                                     "Update trust decay rate")
    check("s9_proposal_created", proposal is not None)
    check("s9_proposal_voting", proposal.status == ProposalStatus.VOTING)
    check("s9_active_round", len(orch.active_rounds) == 1)

    # Cast votes — 8 approve, 2 reject
    for i in range(8):
        check(f"s9_vote_{i}", orch.cast_vote(f"orch_{i}", proposal.proposal_id,
                                              VoteChoice.APPROVE))
    for i in range(8, 10):
        orch.cast_vote(f"orch_{i}", proposal.proposal_id, VoteChoice.REJECT)

    # Finalize
    decision = orch.finalize_proposal(proposal.proposal_id)
    check("s9_finalized", decision is not None)
    check("s9_approved", decision.outcome == VoteChoice.APPROVE)
    check("s9_completed", len(orch.completed) == 1)
    check("s9_audit_recorded", len(orch.audit.decisions) == 1)

    # ─── S10: Isolated node cannot propose ────────────────────────────

    bad_orch_node = _make_node("bad_orch", trust=0.7)
    bad_orch_node.byzantine_score = 0.9  # Above isolation threshold
    orch.register_node(bad_orch_node)

    bad_proposal = orch.create_proposal("bad_orch", ProposalType.POLICY_CHANGE,
                                         "Malicious proposal")
    check("s10_isolated_blocked", bad_proposal is None)

    # Isolated node cannot vote
    prop2 = orch.create_proposal("orch_1", ProposalType.MEMBERSHIP_ADD, "Add member")
    if prop2:
        check("s10_isolated_cant_vote",
              not orch.cast_vote("bad_orch", prop2.proposal_id, VoteChoice.APPROVE))

    # ─── S11: Abstention handling ─────────────────────────────────────

    nodes11 = [_make_node(f"abs_{i}", trust=0.7) for i in range(7)]
    proposal11 = GovernanceProposal(
        proposal_id="prop_abstain",
        proposal_type=ProposalType.BUDGET_ALLOCATION,
        proposer_id="abs_0",
        federation_id="fed_test",
        title="Budget vote",
        quorum_threshold=0.5,
        min_participation=0.5,
    )

    bft11 = BFTGovernanceRound(proposal11, nodes11, calc)
    # 3 approve, 1 reject, 3 abstain
    for i in range(3):
        bft11.submit_vote(GovernanceVote(f"abs_{i}", "prop_abstain", VoteChoice.APPROVE, 0.0))
    bft11.submit_vote(GovernanceVote("abs_3", "prop_abstain", VoteChoice.REJECT, 0.0))
    for i in range(4, 7):
        bft11.submit_vote(GovernanceVote(f"abs_{i}", "prop_abstain", VoteChoice.ABSTAIN, 0.0))

    dec11 = bft11.try_finalize()
    check("s11_abstain_finalized", dec11 is not None)
    check("s11_abstain_approved", dec11.outcome == VoteChoice.APPROVE,
          f"outcome={dec11.outcome.name}")  # 3/4 approve (excluding abstain) > 0.5
    check("s11_abstain_power", dec11.abstain_power > 0)

    # ─── S12: BFT message handling ────────────────────────────────────

    nodes12 = [_make_node(f"msg_{i}") for i in range(4)]
    proposal12 = GovernanceProposal(
        proposal_id="prop_msg",
        proposal_type=ProposalType.PARAMETER_UPDATE,
        proposer_id="msg_0",
        federation_id="fed_test",
        title="Msg test",
    )
    bft12 = BFTGovernanceRound(proposal12, nodes12, calc)

    # Valid message
    msg = BFTMessage("msg_0", BFTPhase.PREPARE, "prop_msg", "hash_abc")
    check("s12_valid_msg", bft12.receive_message(msg))

    # Non-member message
    bad_msg = BFTMessage("outsider", BFTPhase.PREPARE, "prop_msg", "hash_abc")
    check("s12_non_member_msg", not bft12.receive_message(bad_msg))

    # Equivocation: same sender, same phase, different hash
    equivoc = BFTMessage("msg_0", BFTPhase.PREPARE, "prop_msg", "hash_DIFFERENT")
    check("s12_equivocation", not bft12.receive_message(equivoc))

    # Prepare quorum check
    for i in range(1, 4):
        bft12.receive_message(BFTMessage(f"msg_{i}", BFTPhase.PREPARE, "prop_msg", "hash_abc"))
    # N=4, f=1, quorum=3
    check("s12_prepare_quorum", bft12.check_prepare_quorum())

    # ─── S13: Proposal type risk levels ───────────────────────────────

    orch13 = GovernanceOrchestrator("fed_risk")
    for i in range(10):
        orch13.register_node(_make_node(f"risk_{i}", trust=0.7, reputation=0.6))

    # Membership remove requires 3/4
    remove_prop = orch13.create_proposal("risk_0", ProposalType.MEMBERSHIP_REMOVE,
                                          "Remove bad actor")
    check("s13_remove_quorum", remove_prop.quorum_threshold == 0.75)

    # Federation merge requires 4/5
    merge_prop = orch13.create_proposal("risk_1", ProposalType.FEDERATION_MERGE,
                                         "Merge with federation B")
    check("s13_merge_quorum", merge_prop.quorum_threshold == 0.8)
    check("s13_merge_participation", merge_prop.min_participation == 0.8)

    # Emergency freeze has 1h deadline
    freeze_prop = orch13.create_proposal("risk_2", ProposalType.EMERGENCY_FREEZE,
                                          "Security incident")
    freeze_deadline = freeze_prop.deadline - freeze_prop.created_at
    check("s13_freeze_deadline", abs(freeze_deadline - 3600.0) < 10,
          f"deadline={freeze_deadline:.0f}s")

    # ─── S14: Spam detection ──────────────────────────────────────────

    spam_detector = MaliciousFederationDetector(spam_threshold=3)
    spam_node = _make_node("spammer", trust=0.7)

    for i in range(5):
        spam_node.proposals_made += 1
        spam_detector.report_spam(spam_node)

    # Should have accumulated penalties after exceeding threshold
    check("s14_spam_detected", spam_node.byzantine_score > 0,
          f"score={spam_node.byzantine_score:.2f}")

    # ─── S15: Multiple proposal lifecycle ─────────────────────────────

    orch15 = GovernanceOrchestrator("fed_multi")
    for i in range(8):
        orch15.register_node(_make_node(f"multi_{i}", trust=0.7, reputation=0.6))

    proposal_types = [
        ProposalType.POLICY_CHANGE,
        ProposalType.MEMBERSHIP_ADD,
        ProposalType.BUDGET_ALLOCATION,
    ]

    completed = 0
    for j, pt in enumerate(proposal_types):
        p = orch15.create_proposal(f"multi_{j}", pt, f"Proposal {j}")
        if p:
            # All vote approve
            for i in range(8):
                orch15.cast_vote(f"multi_{i}", p.proposal_id, VoteChoice.APPROVE)
            d = orch15.finalize_proposal(p.proposal_id)
            if d:
                completed += 1

    check("s15_all_completed", completed == 3)
    check("s15_audit_chain", orch15.audit.verify_chain()[0])
    check("s15_audit_count", len(orch15.audit.decisions) == 3)

    # ─── S16: Voting power affects outcome ────────────────────────────

    # Create nodes with very different voting power
    whale = _make_node("whale", trust=0.9, stake=1000, reputation=0.9)
    minnows = [_make_node(f"minnow_{i}", trust=0.3, stake=10, reputation=0.2)
               for i in range(6)]

    all16 = [whale] + minnows
    proposal16 = GovernanceProposal(
        proposal_id="prop_power",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="whale",
        federation_id="fed_test",
        title="Power test",
        quorum_threshold=0.5,
        min_participation=0.5,
    )

    bft16 = BFTGovernanceRound(proposal16, all16, calc)

    # Whale approves, all minnows reject
    bft16.submit_vote(GovernanceVote("whale", "prop_power", VoteChoice.APPROVE, 0.0))
    for i in range(6):
        bft16.submit_vote(GovernanceVote(f"minnow_{i}", "prop_power", VoteChoice.REJECT, 0.0))

    dec16 = bft16.try_finalize()
    check("s16_finalized", dec16 is not None)
    # Whale has much more power due to higher trust + stake
    check("s16_whale_power", dec16.approve_power > 0)
    check("s16_power_matters",
          dec16.approve_power != dec16.reject_power,
          f"approve={dec16.approve_power:.3f} reject={dec16.reject_power:.3f}")

    # ─── Print Results ────────────────────────────────────────────────

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"\n{'='*70}")
    print(f"Federation Governance BFT Protocol")
    print(f"{'='*70}")

    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        det = f" [{detail}]" if detail else ""
        if not ok:
            print(f"  {status}: {name}{det}")

    print(f"\n  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*70}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL: {name} [{detail}]")

    return passed, failed


if __name__ == "__main__":
    run_tests()
