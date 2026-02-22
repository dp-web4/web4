#!/usr/bin/env python3
"""
Web4 SAL Appeals Mechanism — Trust Penalty Appeals Reference Implementation

Addresses the critical gap identified by 4-life visitors and Nova review:
"Web4 does not yet have a formal appeals mechanism for false positive trust penalties."

SAL spec §5.5: "Negative adjustments MUST include appeal path and cool-down period."

Design principles:
1. Cool-down enforcement (spec mandate)
2. Evidence challenge mechanism
3. Multi-tier appeals (entity → auditor → society → federation)
4. Witness quorum for appeal decisions
5. Anti-gaming (forgiveness exploitation protection per adversarial taxonomy)
6. Expungement with conditions (Nova recommendation)
7. Rollback semantics for successful appeals
8. ATP staking to prevent frivolous appeals

Spec refs:
  web4-standard/core-spec/web4-society-authority-law.md §5.5
  adversarials/TAXONOMY.md (forgiveness exploitation)
  forum/nova/nova-web4-furhter-review.md (appeals + expungement)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── Appeal States ────────────────────────────────────────────────────

class AppealState(str, Enum):
    FILED = "filed"              # Appeal submitted, awaiting review
    UNDER_REVIEW = "under_review"  # Being reviewed by authority
    EVIDENCE_REQUESTED = "evidence_requested"  # Additional evidence needed
    DECIDED = "decided"          # Final decision rendered
    ESCALATED = "escalated"      # Sent to higher authority
    WITHDRAWN = "withdrawn"      # Appellant withdrew
    EXPIRED = "expired"          # Appeal window expired


class AppealDecision(str, Enum):
    UPHELD = "upheld"            # Original penalty stands
    PARTIALLY_REVERSED = "partially_reversed"  # Some dimensions restored
    FULLY_REVERSED = "fully_reversed"  # Complete rollback
    MODIFIED = "modified"        # Different penalty applied


class AppealTier(str, Enum):
    TIER_1_AUDITOR = "tier_1_auditor"       # Original auditor reconsideration
    TIER_2_SOCIETY = "tier_2_society"        # Society authority review
    TIER_3_FEDERATION = "tier_3_federation"  # Federation arbitration


# ── Penalty Record ──────────────────────────────────────────────────

@dataclass
class TensorSnapshot:
    """Snapshot of T3/V3 before and after a penalty."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5
    valuation: float = 0.0
    veracity: float = 0.5
    validity: float = 0.5

    def t3_composite(self) -> float:
        return self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3

    def to_dict(self) -> dict:
        return {
            "talent": self.talent, "training": self.training,
            "temperament": self.temperament, "valuation": self.valuation,
            "veracity": self.veracity, "validity": self.validity,
        }


@dataclass
class PenaltyRecord:
    """A recorded trust penalty that can be appealed."""
    penalty_id: str
    target_lct: str
    auditor_lct: str
    timestamp: float
    reason: str
    evidence_hash: str
    pre_penalty: TensorSnapshot
    post_penalty: TensorSnapshot
    cool_down_seconds: float = 86400.0  # 24 hours default
    appeal_window_seconds: float = 604800.0  # 7 days
    appealed: bool = False

    @property
    def appeal_deadline(self) -> float:
        return self.timestamp + self.appeal_window_seconds

    @property
    def cool_down_expires(self) -> float:
        return self.timestamp + self.cool_down_seconds

    def is_within_appeal_window(self, now: Optional[float] = None) -> bool:
        return (now or time.time()) <= self.appeal_deadline

    def is_in_cool_down(self, now: Optional[float] = None) -> bool:
        return (now or time.time()) <= self.cool_down_expires


# ── Appeal Record ────────────────────────────────────────────────────

@dataclass
class AppealRecord:
    """Complete appeal record."""
    appeal_id: str
    penalty_id: str
    appellant_lct: str
    tier: AppealTier
    state: AppealState
    filed_at: float
    grounds: str
    counter_evidence: List[str]  # evidence hashes
    atp_stake: float
    reviewer_lct: Optional[str] = None
    decision: Optional[AppealDecision] = None
    decision_reason: Optional[str] = None
    decided_at: Optional[float] = None
    restored_tensor: Optional[TensorSnapshot] = None
    escalation_history: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "appeal_id": self.appeal_id,
            "penalty_id": self.penalty_id,
            "appellant_lct": self.appellant_lct,
            "tier": self.tier.value,
            "state": self.state.value,
            "filed_at": self.filed_at,
            "grounds": self.grounds,
            "counter_evidence": self.counter_evidence,
            "atp_stake": self.atp_stake,
            "reviewer_lct": self.reviewer_lct,
            "decision": self.decision.value if self.decision else None,
            "decision_reason": self.decision_reason,
            "decided_at": self.decided_at,
        }


# ── Anti-Gaming: Forgiveness Exploitation ────────────────────────────

@dataclass
class AppealHistory:
    """Track appeal patterns per entity to detect gaming."""
    total_appeals: int = 0
    total_penalties: int = 0
    successful_appeals: int = 0
    failed_appeals: int = 0
    last_appeal_ts: float = 0.0
    appeal_streak: int = 0  # consecutive successful appeals

    @property
    def success_rate(self) -> float:
        if self.total_appeals == 0:
            return 0.0
        return self.successful_appeals / self.total_appeals

    @property
    def penalty_appeal_ratio(self) -> float:
        """Ratio of appeals to penalties. High = gaming signal."""
        if self.total_penalties == 0:
            return 0.0
        return self.total_appeals / self.total_penalties

    @property
    def is_suspicious(self) -> bool:
        """Detect forgiveness exploitation pattern.

        Per adversarial taxonomy: "Build trust → violate → appeal → repeat"
        Suspicious if: high appeal rate AND high success rate AND high penalty rate
        """
        if self.total_appeals < 3:
            return False
        # Too many consecutive successful appeals (gaming pattern)
        if self.appeal_streak >= 3:
            return True
        # Appeals > 50% of penalties
        if self.penalty_appeal_ratio > 0.5 and self.total_appeals >= 5:
            return True
        return False


class ForgivenesExploitationDetector:
    """Detect the "build trust → violate → appeal → repeat" pattern."""

    APPEAL_COOLDOWN_S = 86400  # 24h between appeals
    MAX_CONSECUTIVE_SUCCESSES = 3
    SUSPICION_THRESHOLD = 0.5

    def __init__(self):
        self._histories: Dict[str, AppealHistory] = {}

    def get_history(self, lct_id: str) -> AppealHistory:
        if lct_id not in self._histories:
            self._histories[lct_id] = AppealHistory()
        return self._histories[lct_id]

    def record_penalty(self, lct_id: str):
        h = self.get_history(lct_id)
        h.total_penalties += 1

    def record_appeal(self, lct_id: str, was_successful: bool):
        h = self.get_history(lct_id)
        h.total_appeals += 1
        h.last_appeal_ts = time.time()
        if was_successful:
            h.successful_appeals += 1
            h.appeal_streak += 1
        else:
            h.failed_appeals += 1
            h.appeal_streak = 0

    def can_appeal(self, lct_id: str, now: Optional[float] = None) -> Tuple[bool, str]:
        h = self.get_history(lct_id)
        now = now or time.time()

        if h.is_suspicious:
            return False, "Appeal pattern suspicious (possible forgiveness exploitation)"

        if h.last_appeal_ts > 0 and (now - h.last_appeal_ts) < self.APPEAL_COOLDOWN_S:
            remaining = self.APPEAL_COOLDOWN_S - (now - h.last_appeal_ts)
            return False, f"Appeal cooldown active ({remaining:.0f}s remaining)"

        return True, "OK"


# ── ATP Appeal Staking ───────────────────────────────────────────────

class AppealStakeManager:
    """ATP staking for appeals — prevents frivolous submissions."""

    TIER_1_STAKE = 5.0    # Low cost for reconsideration
    TIER_2_STAKE = 15.0   # Medium cost for society review
    TIER_3_STAKE = 50.0   # High cost for federation arbitration

    def __init__(self):
        self._balances: Dict[str, float] = {}
        self._staked: Dict[str, float] = {}  # appeal_id → staked amount

    def set_balance(self, lct_id: str, balance: float):
        self._balances[lct_id] = balance

    def get_balance(self, lct_id: str) -> float:
        return self._balances.get(lct_id, 0.0)

    def required_stake(self, tier: AppealTier) -> float:
        return {
            AppealTier.TIER_1_AUDITOR: self.TIER_1_STAKE,
            AppealTier.TIER_2_SOCIETY: self.TIER_2_STAKE,
            AppealTier.TIER_3_FEDERATION: self.TIER_3_STAKE,
        }[tier]

    def stake(self, appeal_id: str, lct_id: str, tier: AppealTier) -> Tuple[bool, str]:
        required = self.required_stake(tier)
        balance = self.get_balance(lct_id)
        if balance < required:
            return False, f"Insufficient ATP: need {required}, have {balance}"
        self._balances[lct_id] -= required
        self._staked[appeal_id] = required
        return True, f"Staked {required} ATP"

    def refund(self, appeal_id: str, lct_id: str):
        """Refund stake on successful appeal."""
        amount = self._staked.pop(appeal_id, 0.0)
        self._balances[lct_id] = self._balances.get(lct_id, 0.0) + amount
        return amount

    def forfeit(self, appeal_id: str):
        """Forfeit stake on failed appeal (burned)."""
        self._staked.pop(appeal_id, 0.0)


# ── Witness Quorum for Appeals ───────────────────────────────────────

@dataclass
class AppealWitnessVote:
    """A witness's vote on an appeal."""
    witness_lct: str
    vote: AppealDecision
    confidence: float  # 0.0-1.0
    reasoning: str
    timestamp: float


class AppealWitnessQuorum:
    """Witness-based quorum for appeal decisions."""

    MIN_WITNESSES = 3
    QUORUM_THRESHOLD = 0.67  # 2/3 majority

    def __init__(self):
        self._votes: Dict[str, List[AppealWitnessVote]] = {}

    def cast_vote(self, appeal_id: str, vote: AppealWitnessVote):
        if appeal_id not in self._votes:
            self._votes[appeal_id] = []
        # Prevent duplicate votes
        if any(v.witness_lct == vote.witness_lct for v in self._votes[appeal_id]):
            return False, "Witness already voted"
        self._votes[appeal_id].append(vote)
        return True, "Vote recorded"

    def get_votes(self, appeal_id: str) -> List[AppealWitnessVote]:
        return self._votes.get(appeal_id, [])

    def has_quorum(self, appeal_id: str) -> bool:
        return len(self.get_votes(appeal_id)) >= self.MIN_WITNESSES

    def tally(self, appeal_id: str) -> Tuple[Optional[AppealDecision], float]:
        """Tally votes and return majority decision with confidence."""
        votes = self.get_votes(appeal_id)
        if len(votes) < self.MIN_WITNESSES:
            return None, 0.0

        # Count weighted votes per decision
        decision_weights: Dict[AppealDecision, float] = {}
        for v in votes:
            decision_weights[v.vote] = decision_weights.get(v.vote, 0.0) + v.confidence

        total_weight = sum(decision_weights.values())
        if total_weight == 0:
            return None, 0.0

        # Find majority
        best_decision = max(decision_weights, key=lambda d: decision_weights[d])
        best_weight = decision_weights[best_decision] / total_weight

        if best_weight >= self.QUORUM_THRESHOLD:
            return best_decision, best_weight
        return None, best_weight  # No quorum reached


# ── Cool-Down Manager ────────────────────────────────────────────────

class CoolDownManager:
    """Enforces cool-down periods per SAL §5.5."""

    DEFAULT_COOL_DOWN_S = 86400.0  # 24 hours

    def __init__(self):
        self._active_cooldowns: Dict[str, float] = {}  # lct_id → expiry

    def start_cooldown(self, lct_id: str, duration_s: Optional[float] = None):
        duration = duration_s or self.DEFAULT_COOL_DOWN_S
        self._active_cooldowns[lct_id] = time.time() + duration

    def is_in_cooldown(self, lct_id: str, now: Optional[float] = None) -> bool:
        now = now or time.time()
        expiry = self._active_cooldowns.get(lct_id, 0.0)
        return now < expiry

    def remaining(self, lct_id: str, now: Optional[float] = None) -> float:
        now = now or time.time()
        expiry = self._active_cooldowns.get(lct_id, 0.0)
        return max(0.0, expiry - now)


# ── Expungement System ───────────────────────────────────────────────

class ExpungementEligibility(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE_TOO_RECENT = "too_recent"
    INELIGIBLE_LOW_TRUST = "low_trust"
    INELIGIBLE_PATTERN = "gaming_pattern"
    INELIGIBLE_SEVERITY = "severity_too_high"


@dataclass
class ExpungementRequest:
    """Request to expunge a penalty from record."""
    penalty_id: str
    requestor_lct: str
    grounds: str
    current_t3_composite: float
    time_since_penalty_s: float


class ExpungementPolicy:
    """Conditions under which penalties can be expunged (Nova recommendation)."""

    MIN_TIME_S = 2592000.0  # 30 days minimum
    MIN_T3_COMPOSITE = 0.6  # Must have recovered trust
    MAX_PENALTY_SEVERITY = 0.2  # Can't expunge severe penalties (>0.2 delta)

    def evaluate(self, request: ExpungementRequest,
                 penalty: PenaltyRecord,
                 gaming_detector: ForgivenesExploitationDetector) -> Tuple[ExpungementEligibility, str]:

        # Time gate
        if request.time_since_penalty_s < self.MIN_TIME_S:
            days = self.MIN_TIME_S / 86400
            return (ExpungementEligibility.INELIGIBLE_TOO_RECENT,
                    f"Must wait {days:.0f} days (only {request.time_since_penalty_s/86400:.0f} passed)")

        # Trust gate
        if request.current_t3_composite < self.MIN_T3_COMPOSITE:
            return (ExpungementEligibility.INELIGIBLE_LOW_TRUST,
                    f"T3 composite {request.current_t3_composite:.2f} < {self.MIN_T3_COMPOSITE}")

        # Severity gate
        t3_delta = abs(penalty.pre_penalty.t3_composite() - penalty.post_penalty.t3_composite())
        if t3_delta > self.MAX_PENALTY_SEVERITY:
            return (ExpungementEligibility.INELIGIBLE_SEVERITY,
                    f"Penalty severity {t3_delta:.2f} > {self.MAX_PENALTY_SEVERITY}")

        # Gaming gate
        history = gaming_detector.get_history(request.requestor_lct)
        if history.is_suspicious:
            return (ExpungementEligibility.INELIGIBLE_PATTERN,
                    "Suspicious appeal pattern detected")

        return ExpungementEligibility.ELIGIBLE, "Eligible for expungement"


# ── Appeals Manager (Orchestrator) ───────────────────────────────────

class AppealsManager:
    """Unified appeals lifecycle manager."""

    def __init__(self):
        self._penalties: Dict[str, PenaltyRecord] = {}
        self._appeals: Dict[str, AppealRecord] = {}
        self.gaming_detector = ForgivenesExploitationDetector()
        self.stake_manager = AppealStakeManager()
        self.witness_quorum = AppealWitnessQuorum()
        self.cooldown = CoolDownManager()
        self.expungement = ExpungementPolicy()
        self._appeal_counter = 0

    def record_penalty(self, penalty: PenaltyRecord):
        """Record a penalty for potential appeal."""
        self._penalties[penalty.penalty_id] = penalty
        self.gaming_detector.record_penalty(penalty.target_lct)
        self.cooldown.start_cooldown(penalty.target_lct, penalty.cool_down_seconds)

    def file_appeal(self, penalty_id: str, appellant_lct: str,
                    grounds: str, counter_evidence: List[str],
                    tier: AppealTier = AppealTier.TIER_1_AUDITOR,
                    now: Optional[float] = None,
                    is_escalation: bool = False) -> Tuple[bool, str, Optional[AppealRecord]]:
        """File an appeal against a penalty."""
        now = now or time.time()

        # Check penalty exists
        penalty = self._penalties.get(penalty_id)
        if not penalty:
            return False, f"Penalty {penalty_id} not found", None

        # Check appeal window
        if not penalty.is_within_appeal_window(now):
            return False, "Appeal window expired", None

        # Check already appealed at this tier
        existing = [a for a in self._appeals.values()
                    if a.penalty_id == penalty_id and a.tier == tier
                    and a.state not in (AppealState.WITHDRAWN, AppealState.EXPIRED)]
        if existing:
            return False, f"Active appeal already exists at {tier.value}", None

        # Check gaming detection (skip for escalations — same dispute)
        if not is_escalation:
            ok, msg = self.gaming_detector.can_appeal(appellant_lct, now)
            if not ok:
                return False, msg, None

        # Stake ATP
        self._appeal_counter += 1
        appeal_id = f"appeal-{self._appeal_counter:04d}"
        ok, msg = self.stake_manager.stake(appeal_id, appellant_lct, tier)
        if not ok:
            return False, msg, None

        appeal = AppealRecord(
            appeal_id=appeal_id,
            penalty_id=penalty_id,
            appellant_lct=appellant_lct,
            tier=tier,
            state=AppealState.FILED,
            filed_at=now,
            grounds=grounds,
            counter_evidence=counter_evidence,
            atp_stake=self.stake_manager.required_stake(tier),
        )

        self._appeals[appeal_id] = appeal
        penalty.appealed = True
        return True, "Appeal filed", appeal

    def review_appeal(self, appeal_id: str, reviewer_lct: str) -> Tuple[bool, str]:
        """Mark an appeal as under review."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found"
        if appeal.state != AppealState.FILED:
            return False, f"Cannot review appeal in state {appeal.state.value}"

        appeal.state = AppealState.UNDER_REVIEW
        appeal.reviewer_lct = reviewer_lct
        return True, "Appeal under review"

    def decide_appeal(self, appeal_id: str, decision: AppealDecision,
                      reason: str,
                      restored_tensor: Optional[TensorSnapshot] = None,
                      now: Optional[float] = None) -> Tuple[bool, str]:
        """Render a decision on an appeal."""
        now = now or time.time()
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found"
        if appeal.state not in (AppealState.UNDER_REVIEW, AppealState.EVIDENCE_REQUESTED):
            return False, f"Cannot decide appeal in state {appeal.state.value}"

        appeal.state = AppealState.DECIDED
        appeal.decision = decision
        appeal.decision_reason = reason
        appeal.decided_at = now

        # Handle stake based on decision
        was_successful = decision in (AppealDecision.FULLY_REVERSED,
                                       AppealDecision.PARTIALLY_REVERSED)

        if was_successful:
            # Refund stake on success
            self.stake_manager.refund(appeal.appeal_id, appeal.appellant_lct)
            if restored_tensor:
                appeal.restored_tensor = restored_tensor
        else:
            # Forfeit stake on failure
            self.stake_manager.forfeit(appeal.appeal_id)

        # Update gaming detector
        self.gaming_detector.record_appeal(appeal.appellant_lct, was_successful)

        return True, f"Decision: {decision.value}"

    def escalate_appeal(self, appeal_id: str,
                        now: Optional[float] = None) -> Tuple[bool, str, Optional[AppealRecord]]:
        """Escalate a decided appeal to a higher tier."""
        now = now or time.time()
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found", None

        if appeal.state != AppealState.DECIDED:
            return False, "Can only escalate decided appeals", None

        if appeal.decision in (AppealDecision.FULLY_REVERSED,):
            return False, "Cannot escalate a fully reversed appeal", None

        # Determine next tier
        next_tier = {
            AppealTier.TIER_1_AUDITOR: AppealTier.TIER_2_SOCIETY,
            AppealTier.TIER_2_SOCIETY: AppealTier.TIER_3_FEDERATION,
        }.get(appeal.tier)

        if not next_tier:
            return False, "No higher tier available (federation is final)", None

        # File new appeal at higher tier
        appeal.state = AppealState.ESCALATED
        appeal.escalation_history.append(f"Escalated from {appeal.tier.value} to {next_tier.value}")

        return self.file_appeal(
            penalty_id=appeal.penalty_id,
            appellant_lct=appeal.appellant_lct,
            grounds=f"Escalation: {appeal.grounds}",
            counter_evidence=appeal.counter_evidence,
            tier=next_tier,
            now=now,
            is_escalation=True,
        )

    def decide_by_quorum(self, appeal_id: str,
                         now: Optional[float] = None) -> Tuple[bool, str]:
        """Decide an appeal based on witness quorum votes."""
        now = now or time.time()
        if not self.witness_quorum.has_quorum(appeal_id):
            return False, "Quorum not reached"

        decision, confidence = self.witness_quorum.tally(appeal_id)
        if decision is None:
            return False, f"No majority reached (best confidence: {confidence:.2f})"

        return self.decide_appeal(
            appeal_id, decision,
            f"Quorum decision (confidence: {confidence:.2f})",
            now=now,
        )

    def request_expungement(self, penalty_id: str, requestor_lct: str,
                            current_t3: float,
                            time_elapsed_s: float) -> Tuple[bool, str]:
        """Request expungement of a penalty record."""
        penalty = self._penalties.get(penalty_id)
        if not penalty:
            return False, "Penalty not found"

        req = ExpungementRequest(
            penalty_id=penalty_id,
            requestor_lct=requestor_lct,
            grounds="Time-based expungement",
            current_t3_composite=current_t3,
            time_since_penalty_s=time_elapsed_s,
        )

        eligibility, reason = self.expungement.evaluate(req, penalty, self.gaming_detector)
        if eligibility != ExpungementEligibility.ELIGIBLE:
            return False, f"Not eligible: {reason}"

        return True, "Eligible for expungement"

    def get_appeal(self, appeal_id: str) -> Optional[AppealRecord]:
        return self._appeals.get(appeal_id)

    def get_appeals_for_penalty(self, penalty_id: str) -> List[AppealRecord]:
        return [a for a in self._appeals.values() if a.penalty_id == penalty_id]

    def get_all_penalties(self) -> List[PenaltyRecord]:
        return list(self._penalties.values())


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    now = time.time()

    # ── T1: Penalty Recording ────────────────────────────────────
    print("T1: Penalty Recording")
    mgr = AppealsManager()
    pre = TensorSnapshot(talent=0.8, training=0.7, temperament=0.9)
    post = TensorSnapshot(talent=0.7, training=0.6, temperament=0.85)
    penalty = PenaltyRecord(
        penalty_id="penalty-001",
        target_lct="lct:web4:human:alice",
        auditor_lct="lct:web4:oracle:auditor1",
        timestamp=now,
        reason="Policy violation: exceeded rate limit",
        evidence_hash="sha256:abc123",
        pre_penalty=pre,
        post_penalty=post,
        cool_down_seconds=3600,  # 1 hour
        appeal_window_seconds=604800,  # 7 days
    )
    mgr.record_penalty(penalty)
    check("T1.1 Penalty recorded", "penalty-001" in mgr._penalties)
    check("T1.2 Pre-penalty T3 composite ≈ 0.8",
          abs(pre.t3_composite() - 0.8) < 0.001)
    check("T1.3 Post-penalty T3 composite < pre",
          post.t3_composite() < pre.t3_composite())
    check("T1.4 Penalty is within appeal window",
          penalty.is_within_appeal_window(now))
    check("T1.5 Cool-down is active",
          mgr.cooldown.is_in_cooldown("lct:web4:human:alice", now))
    check("T1.6 Penalty not yet appealed", not penalty.appealed)
    check("T1.7 Penalty has evidence hash", penalty.evidence_hash == "sha256:abc123")

    # ── T2: Filing Appeals ───────────────────────────────────────
    print("T2: Filing Appeals")
    mgr.stake_manager.set_balance("lct:web4:human:alice", 100.0)
    ok, msg, appeal = mgr.file_appeal(
        "penalty-001", "lct:web4:human:alice",
        "Evidence was misinterpreted — rate limit was per-minute not per-hour",
        ["sha256:counter_evidence_1"],
        AppealTier.TIER_1_AUDITOR,
        now=now,
    )
    check("T2.1 Appeal filed successfully", ok)
    check("T2.2 Appeal record created", appeal is not None)
    check("T2.3 Appeal state is FILED", appeal.state == AppealState.FILED)
    check("T2.4 Appeal tier is TIER_1", appeal.tier == AppealTier.TIER_1_AUDITOR)
    check("T2.5 ATP staked (5.0 for tier 1)", appeal.atp_stake == 5.0)
    check("T2.6 Balance reduced", mgr.stake_manager.get_balance("lct:web4:human:alice") == 95.0)
    check("T2.7 Penalty marked as appealed", penalty.appealed)
    check("T2.8 Counter evidence recorded", len(appeal.counter_evidence) == 1)

    # Can't file duplicate appeal
    ok2, msg2, _ = mgr.file_appeal(
        "penalty-001", "lct:web4:human:alice",
        "Same appeal again", [], AppealTier.TIER_1_AUDITOR, now=now,
    )
    check("T2.9 Duplicate appeal rejected", not ok2)
    check("T2.10 Error mentions 'already exists'", "already exists" in msg2)

    # ── T3: Appeal Review ────────────────────────────────────────
    print("T3: Appeal Review")
    ok, msg = mgr.review_appeal(appeal.appeal_id, "lct:web4:oracle:auditor1")
    check("T3.1 Review started", ok)
    check("T3.2 State is UNDER_REVIEW", appeal.state == AppealState.UNDER_REVIEW)
    check("T3.3 Reviewer assigned", appeal.reviewer_lct == "lct:web4:oracle:auditor1")

    # Can't review again
    ok2, _ = mgr.review_appeal(appeal.appeal_id, "lct:web4:oracle:auditor2")
    check("T3.4 Can't review twice", not ok2)

    # ── T4: Appeal Decisions ─────────────────────────────────────
    print("T4: Appeal Decisions")
    restored = TensorSnapshot(talent=0.75, training=0.65, temperament=0.87)
    ok, msg = mgr.decide_appeal(
        appeal.appeal_id, AppealDecision.PARTIALLY_REVERSED,
        "Rate limit interpretation corrected; partial restoration",
        restored_tensor=restored,
        now=now,
    )
    check("T4.1 Decision rendered", ok)
    check("T4.2 State is DECIDED", appeal.state == AppealState.DECIDED)
    check("T4.3 Decision is PARTIALLY_REVERSED",
          appeal.decision == AppealDecision.PARTIALLY_REVERSED)
    check("T4.4 Decision reason recorded", "corrected" in appeal.decision_reason)
    check("T4.5 Restored tensor recorded", appeal.restored_tensor is not None)
    check("T4.6 Stake refunded (successful appeal)",
          mgr.stake_manager.get_balance("lct:web4:human:alice") == 100.0)

    # ── T5: Appeal Escalation ────────────────────────────────────
    print("T5: Appeal Escalation")
    # File a new penalty and appeal that gets upheld
    pre2 = TensorSnapshot(talent=0.6, training=0.5, temperament=0.7)
    post2 = TensorSnapshot(talent=0.5, training=0.4, temperament=0.65)
    penalty2 = PenaltyRecord(
        penalty_id="penalty-002",
        target_lct="lct:web4:ai:bob",
        auditor_lct="lct:web4:oracle:auditor1",
        timestamp=now,
        reason="Misleading output",
        evidence_hash="sha256:def456",
        pre_penalty=pre2,
        post_penalty=post2,
    )
    mgr.record_penalty(penalty2)
    mgr.stake_manager.set_balance("lct:web4:ai:bob", 200.0)

    ok, _, appeal2 = mgr.file_appeal(
        "penalty-002", "lct:web4:ai:bob",
        "Output was not misleading, context was missing",
        ["sha256:bob_evidence_1"],
        AppealTier.TIER_1_AUDITOR,
        now=now,
    )
    check("T5.1 Bob's appeal filed", ok)

    mgr.review_appeal(appeal2.appeal_id, "lct:web4:oracle:auditor1")
    mgr.decide_appeal(appeal2.appeal_id, AppealDecision.UPHELD,
                       "Evidence insufficient", now=now)
    check("T5.2 Appeal upheld", appeal2.decision == AppealDecision.UPHELD)
    check("T5.3 Stake forfeited",
          mgr.stake_manager.get_balance("lct:web4:ai:bob") == 195.0)

    # Escalate to tier 2
    ok, msg, appeal3 = mgr.escalate_appeal(appeal2.appeal_id, now=now)
    check("T5.4 Escalation successful", ok)
    check("T5.5 New appeal at tier 2", appeal3.tier == AppealTier.TIER_2_SOCIETY)
    check("T5.6 Original marked ESCALATED", appeal2.state == AppealState.ESCALATED)
    check("T5.7 Higher stake (15 ATP for tier 2)", appeal3.atp_stake == 15.0)
    check("T5.8 Balance reduced further",
          mgr.stake_manager.get_balance("lct:web4:ai:bob") == 180.0)

    # ── T6: Witness Quorum Voting ────────────────────────────────
    print("T6: Witness Quorum Voting")
    # Use tier 2 appeal for quorum voting
    mgr.review_appeal(appeal3.appeal_id, "lct:web4:authority:society1")

    # Cast 3 votes
    votes = [
        AppealWitnessVote("lct:web4:oracle:w1", AppealDecision.FULLY_REVERSED,
                          0.8, "Evidence compelling", now),
        AppealWitnessVote("lct:web4:oracle:w2", AppealDecision.FULLY_REVERSED,
                          0.7, "Agree with appellant", now),
        AppealWitnessVote("lct:web4:oracle:w3", AppealDecision.UPHELD,
                          0.5, "Insufficient proof", now),
    ]
    for v in votes:
        ok, _ = mgr.witness_quorum.cast_vote(appeal3.appeal_id, v)
        check(f"T6.{votes.index(v)+1} Vote cast by {v.witness_lct.split(':')[-1]}", ok)

    check("T6.4 Quorum reached", mgr.witness_quorum.has_quorum(appeal3.appeal_id))

    decision, confidence = mgr.witness_quorum.tally(appeal3.appeal_id)
    check("T6.5 Majority is FULLY_REVERSED", decision == AppealDecision.FULLY_REVERSED)
    check("T6.6 Confidence > 0.67", confidence > 0.67)

    ok, msg = mgr.decide_by_quorum(appeal3.appeal_id, now=now)
    check("T6.7 Quorum decision applied", ok)
    check("T6.8 Appeal decided by quorum", appeal3.state == AppealState.DECIDED)
    check("T6.9 Decision is FULLY_REVERSED",
          appeal3.decision == AppealDecision.FULLY_REVERSED)
    check("T6.10 Stake refunded",
          mgr.stake_manager.get_balance("lct:web4:ai:bob") == 195.0)

    # Duplicate vote rejected
    ok, msg = mgr.witness_quorum.cast_vote(
        appeal3.appeal_id,
        AppealWitnessVote("lct:web4:oracle:w1", AppealDecision.UPHELD, 1.0, "Changed mind", now)
    )
    check("T6.11 Duplicate vote rejected", not ok)

    # ── T7: Gaming Detection ────────────────────────────────────
    print("T7: Gaming Detection")
    detector = ForgivenesExploitationDetector()

    # Normal pattern: a few appeals
    for _ in range(2):
        detector.record_appeal("lct:web4:gamer:innocent", True)
    h = detector.get_history("lct:web4:gamer:innocent")
    check("T7.1 Two successful appeals not suspicious", not h.is_suspicious)

    # Gaming pattern: 3 consecutive successes
    detector.record_appeal("lct:web4:gamer:innocent", True)
    check("T7.2 Three consecutive successes IS suspicious", h.is_suspicious)

    # Reset streak with a failure
    detector.record_appeal("lct:web4:gamer:innocent", False)
    check("T7.3 Failed appeal resets streak", h.appeal_streak == 0)
    check("T7.4 No longer suspicious after failure", not h.is_suspicious)

    # High appeal ratio detection
    heavy_appealer = ForgivenesExploitationDetector()
    for _ in range(3):
        heavy_appealer.record_penalty("lct:web4:gamer:heavy")
    for i in range(5):
        heavy_appealer.record_appeal("lct:web4:gamer:heavy", i % 2 == 0)
    h2 = heavy_appealer.get_history("lct:web4:gamer:heavy")
    check("T7.5 High appeal ratio flagged", h2.penalty_appeal_ratio > 0.5)
    check("T7.6 Heavy appealer suspicious", h2.is_suspicious)

    # Appeal cooldown enforcement
    cd_detector = ForgivenesExploitationDetector()
    cd_detector.record_appeal("lct:web4:test:cooldown", True)
    ok, msg = cd_detector.can_appeal("lct:web4:test:cooldown", now)
    check("T7.7 Cooldown active after appeal", not ok)
    check("T7.8 Cooldown message mentions remaining", "remaining" in msg)

    # After cooldown expires
    ok, msg = cd_detector.can_appeal("lct:web4:test:cooldown",
                                      now + 86401)  # 24h + 1s
    check("T7.9 Can appeal after cooldown", ok)

    # ── T8: ATP Staking ──────────────────────────────────────────
    print("T8: ATP Staking")
    stakes = AppealStakeManager()
    stakes.set_balance("lct:web4:test:staker", 50.0)

    check("T8.1 Tier 1 stake = 5", stakes.required_stake(AppealTier.TIER_1_AUDITOR) == 5.0)
    check("T8.2 Tier 2 stake = 15", stakes.required_stake(AppealTier.TIER_2_SOCIETY) == 15.0)
    check("T8.3 Tier 3 stake = 50", stakes.required_stake(AppealTier.TIER_3_FEDERATION) == 50.0)

    ok, _ = stakes.stake("test-1", "lct:web4:test:staker", AppealTier.TIER_1_AUDITOR)
    check("T8.4 Tier 1 stake succeeds", ok)
    check("T8.5 Balance reduced by 5", stakes.get_balance("lct:web4:test:staker") == 45.0)

    refund = stakes.refund("test-1", "lct:web4:test:staker")
    check("T8.6 Refund returns 5", refund == 5.0)
    check("T8.7 Balance restored to 50", stakes.get_balance("lct:web4:test:staker") == 50.0)

    # Insufficient balance
    ok, msg = stakes.stake("test-2", "lct:web4:test:poor", AppealTier.TIER_3_FEDERATION)
    check("T8.8 Insufficient balance rejected", not ok)
    check("T8.9 Error mentions ATP", "ATP" in msg)

    # ── T9: Cool-Down Enforcement ────────────────────────────────
    print("T9: Cool-Down Enforcement")
    cd = CoolDownManager()
    cd.start_cooldown("lct:web4:test:cd1", 3600)  # 1 hour
    check("T9.1 Cooldown active", cd.is_in_cooldown("lct:web4:test:cd1", now))
    check("T9.2 Remaining > 0", cd.remaining("lct:web4:test:cd1", now) > 0)
    check("T9.3 Not in cooldown after expiry",
          not cd.is_in_cooldown("lct:web4:test:cd1", now + 3601))
    check("T9.4 Remaining is 0 after expiry",
          cd.remaining("lct:web4:test:cd1", now + 3601) == 0)
    check("T9.5 Unknown entity not in cooldown",
          not cd.is_in_cooldown("lct:web4:test:unknown", now))

    # ── T10: Expungement ─────────────────────────────────────────
    print("T10: Expungement")
    exp_mgr = AppealsManager()
    pre_exp = TensorSnapshot(talent=0.7, training=0.6, temperament=0.8)
    post_exp = TensorSnapshot(talent=0.6, training=0.55, temperament=0.75)
    penalty_exp = PenaltyRecord(
        penalty_id="penalty-exp",
        target_lct="lct:web4:human:charlie",
        auditor_lct="lct:web4:oracle:auditor",
        timestamp=now - 3600000,  # long ago
        reason="Minor policy violation",
        evidence_hash="sha256:exp123",
        pre_penalty=pre_exp,
        post_penalty=post_exp,
    )
    exp_mgr.record_penalty(penalty_exp)

    # Eligible: enough time, good T3, small penalty
    ok, msg = exp_mgr.request_expungement(
        "penalty-exp", "lct:web4:human:charlie",
        current_t3=0.75, time_elapsed_s=3600000,
    )
    check("T10.1 Eligible for expungement", ok)

    # Too recent
    ok, msg = exp_mgr.request_expungement(
        "penalty-exp", "lct:web4:human:charlie",
        current_t3=0.75, time_elapsed_s=86400,
    )
    check("T10.2 Too recent for expungement", not ok)
    check("T10.3 Reason mentions days", "days" in msg)

    # Low trust
    ok, msg = exp_mgr.request_expungement(
        "penalty-exp", "lct:web4:human:charlie",
        current_t3=0.3, time_elapsed_s=3600000,
    )
    check("T10.4 Low trust blocks expungement", not ok)

    # Severe penalty
    severe_pre = TensorSnapshot(talent=0.9, training=0.9, temperament=0.9)
    severe_post = TensorSnapshot(talent=0.4, training=0.4, temperament=0.4)
    severe_penalty = PenaltyRecord(
        penalty_id="penalty-severe",
        target_lct="lct:web4:human:dave",
        auditor_lct="lct:web4:oracle:auditor",
        timestamp=now - 3600000,
        reason="Major ethics violation",
        evidence_hash="sha256:severe",
        pre_penalty=severe_pre,
        post_penalty=severe_post,
    )
    exp_mgr.record_penalty(severe_penalty)
    ok, msg = exp_mgr.request_expungement(
        "penalty-severe", "lct:web4:human:dave",
        current_t3=0.8, time_elapsed_s=3600000,
    )
    check("T10.5 Severe penalty not expungable", not ok)
    check("T10.6 Reason mentions severity", "severity" in msg.lower())

    # ── T11: Full Appeal Lifecycle ───────────────────────────────
    print("T11: Full Appeal Lifecycle")
    lifecycle = AppealsManager()

    # Phase 1: Penalty issued
    pre_lc = TensorSnapshot(talent=0.85, training=0.75, temperament=0.9)
    post_lc = TensorSnapshot(talent=0.75, training=0.65, temperament=0.85)
    penalty_lc = PenaltyRecord(
        penalty_id="penalty-lifecycle",
        target_lct="lct:web4:ai:lifecycle-agent",
        auditor_lct="lct:web4:oracle:lifecycle-auditor",
        timestamp=now,
        reason="False positive: normal behavior flagged",
        evidence_hash="sha256:lifecycle",
        pre_penalty=pre_lc,
        post_penalty=post_lc,
        cool_down_seconds=1800,  # 30 min
        appeal_window_seconds=604800,
    )
    lifecycle.record_penalty(penalty_lc)
    lifecycle.stake_manager.set_balance("lct:web4:ai:lifecycle-agent", 200.0)
    check("T11.1 Penalty recorded", True)

    # Phase 2: Tier 1 appeal (reconsideration)
    ok, _, appeal_lc = lifecycle.file_appeal(
        "penalty-lifecycle", "lct:web4:ai:lifecycle-agent",
        "Behavior was within normal parameters for my role",
        ["sha256:role_history", "sha256:action_logs"],
        AppealTier.TIER_1_AUDITOR,
        now=now,
    )
    check("T11.2 Tier 1 appeal filed", ok)

    lifecycle.review_appeal(appeal_lc.appeal_id, "lct:web4:oracle:lifecycle-auditor")
    lifecycle.decide_appeal(appeal_lc.appeal_id, AppealDecision.UPHELD,
                            "Evidence examined, penalty stands", now=now)
    check("T11.3 Tier 1 upheld", appeal_lc.decision == AppealDecision.UPHELD)

    # Phase 3: Escalate to tier 2
    ok, _, appeal_t2 = lifecycle.escalate_appeal(appeal_lc.appeal_id, now=now)
    check("T11.4 Escalated to tier 2", ok)

    # Phase 4: Witness quorum votes at tier 2
    lifecycle.review_appeal(appeal_t2.appeal_id, "lct:web4:authority:society")

    for i, (decision, conf) in enumerate([
        (AppealDecision.FULLY_REVERSED, 0.9),
        (AppealDecision.FULLY_REVERSED, 0.85),
        (AppealDecision.FULLY_REVERSED, 0.7),
    ]):
        lifecycle.witness_quorum.cast_vote(
            appeal_t2.appeal_id,
            AppealWitnessVote(f"lct:web4:witness:lc-{i}", decision, conf,
                              "Role context confirms normal behavior", now)
        )

    ok, msg = lifecycle.decide_by_quorum(appeal_t2.appeal_id, now=now)
    check("T11.5 Quorum decision applied", ok)
    check("T11.6 Fully reversed by quorum",
          appeal_t2.decision == AppealDecision.FULLY_REVERSED)

    # Phase 5: Check final state
    appeals = lifecycle.get_appeals_for_penalty("penalty-lifecycle")
    check("T11.7 Two appeals on record", len(appeals) == 2)
    check("T11.8 Original is ESCALATED", appeals[0].state == AppealState.ESCALATED)
    check("T11.9 Escalated is DECIDED", appeals[1].state == AppealState.DECIDED)

    balance = lifecycle.stake_manager.get_balance("lct:web4:ai:lifecycle-agent")
    # Started 200, lost 5 (tier 1 forfeited), paid 15 (tier 2), got 15 back (tier 2 refund)
    check("T11.10 Final balance = 195 (5 forfeited from tier 1)", balance == 195.0)

    # ── T12: Appeal Window Expiry ────────────────────────────────
    print("T12: Appeal Window Expiry")
    expired_mgr = AppealsManager()
    expired_penalty = PenaltyRecord(
        penalty_id="penalty-expired",
        target_lct="lct:web4:human:late",
        auditor_lct="lct:web4:oracle:auditor",
        timestamp=now - 700000,  # >7 days ago
        reason="Policy violation",
        evidence_hash="sha256:expired",
        pre_penalty=TensorSnapshot(),
        post_penalty=TensorSnapshot(talent=0.4),
        appeal_window_seconds=604800,
    )
    expired_mgr.record_penalty(expired_penalty)
    expired_mgr.stake_manager.set_balance("lct:web4:human:late", 100.0)

    ok, msg, _ = expired_mgr.file_appeal(
        "penalty-expired", "lct:web4:human:late",
        "I want to appeal", [], now=now,
    )
    check("T12.1 Expired appeal rejected", not ok)
    check("T12.2 Error mentions window", "window" in msg.lower())

    # ── T13: Federation Tier Limits ──────────────────────────────
    print("T13: Federation Tier Limits")
    fed_mgr = AppealsManager()
    fed_penalty = PenaltyRecord(
        penalty_id="penalty-fed",
        target_lct="lct:web4:ai:federation-case",
        auditor_lct="lct:web4:oracle:auditor",
        timestamp=now,
        reason="Cross-society dispute",
        evidence_hash="sha256:fed",
        pre_penalty=TensorSnapshot(),
        post_penalty=TensorSnapshot(talent=0.4),
    )
    fed_mgr.record_penalty(fed_penalty)
    fed_mgr.stake_manager.set_balance("lct:web4:ai:federation-case", 500.0)

    # File and resolve at tier 3
    ok, _, appeal_fed = fed_mgr.file_appeal(
        "penalty-fed", "lct:web4:ai:federation-case",
        "Federation-level dispute", [],
        AppealTier.TIER_3_FEDERATION, now=now,
    )
    check("T13.1 Tier 3 appeal filed", ok)
    check("T13.2 Stake is 50 ATP", appeal_fed.atp_stake == 50.0)

    fed_mgr.review_appeal(appeal_fed.appeal_id, "lct:web4:federation:arbitrator")
    fed_mgr.decide_appeal(appeal_fed.appeal_id, AppealDecision.UPHELD,
                           "Federation confirms penalty", now=now)

    # Can't escalate beyond federation
    ok, msg, _ = fed_mgr.escalate_appeal(appeal_fed.appeal_id, now=now)
    check("T13.3 Can't escalate beyond federation", not ok)
    check("T13.4 Error mentions 'final'", "final" in msg)

    # ── T14: Edge Cases ──────────────────────────────────────────
    print("T14: Edge Cases")

    # Non-existent penalty
    edge_mgr = AppealsManager()
    edge_mgr.stake_manager.set_balance("lct:web4:test:edge", 100.0)
    ok, msg, _ = edge_mgr.file_appeal("nonexistent", "lct:web4:test:edge",
                                       "Appeal nothing", [])
    check("T14.1 Non-existent penalty rejected", not ok)

    # Non-existent appeal review
    ok, msg = edge_mgr.review_appeal("nonexistent-appeal", "reviewer")
    check("T14.2 Non-existent appeal review rejected", not ok)

    # Non-existent appeal decision
    ok, msg = edge_mgr.decide_appeal("nonexistent-appeal", AppealDecision.UPHELD, "")
    check("T14.3 Non-existent appeal decision rejected", not ok)

    # Escalate non-decided appeal
    edge_penalty = PenaltyRecord(
        penalty_id="penalty-edge",
        target_lct="lct:web4:test:edge",
        auditor_lct="lct:web4:oracle:auditor",
        timestamp=now,
        reason="Edge case",
        evidence_hash="sha256:edge",
        pre_penalty=TensorSnapshot(),
        post_penalty=TensorSnapshot(talent=0.4),
    )
    edge_mgr.record_penalty(edge_penalty)
    ok, _, edge_appeal = edge_mgr.file_appeal(
        "penalty-edge", "lct:web4:test:edge", "Test", [],
        now=now,
    )
    ok, msg, _ = edge_mgr.escalate_appeal(edge_appeal.appeal_id, now=now)
    check("T14.4 Can't escalate non-decided appeal", not ok)

    # Expungement non-existent penalty
    ok, msg = edge_mgr.request_expungement("nonexistent", "lct:web4:test:edge", 0.8, 9999999)
    check("T14.5 Non-existent penalty expungement rejected", not ok)

    # Appeal to_dict
    d = appeal.to_dict()
    check("T14.6 Appeal serializable", "appeal_id" in d)
    check("T14.7 Appeal has tier", "tier" in d)
    check("T14.8 Appeal has state", "state" in d)

    # TensorSnapshot to_dict
    ts = TensorSnapshot(talent=0.8, training=0.7, temperament=0.9)
    td = ts.to_dict()
    check("T14.9 Tensor snapshot serializable", "talent" in td)
    check("T14.10 All 6 fields", len(td) == 6)

    # ── T15: Appeal Serialization ────────────────────────────────
    print("T15: Appeal Serialization")
    d = appeal.to_dict()
    check("T15.1 Has penalty_id", d["penalty_id"] == "penalty-001")
    check("T15.2 Has appellant_lct", d["appellant_lct"] == "lct:web4:human:alice")
    check("T15.3 Has tier", d["tier"] == "tier_1_auditor")
    check("T15.4 Has state", d["state"] == "decided")
    check("T15.5 Has decision", d["decision"] == "partially_reversed")
    check("T15.6 Has atp_stake", d["atp_stake"] == 5.0)

    j = json.dumps(d, sort_keys=True)
    parsed = json.loads(j)
    check("T15.7 JSON roundtrip preserves appeal_id", parsed["appeal_id"] == d["appeal_id"])
    check("T15.8 JSON roundtrip preserves decision", parsed["decision"] == d["decision"])

    # ── Summary ──────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"SAL Appeals Mechanism: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  FAILED: {failed}")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
