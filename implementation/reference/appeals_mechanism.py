#!/usr/bin/env python3
"""
Web4 Appeals Mechanism — SAL-Level Trust Penalty Appeals

Addresses the critical gap identified by 4-life visitor:
"Web4 does not yet have a formal appeals mechanism for false positive
trust penalties. Important to acknowledge."

Design at SAL (Society-Authority-Law) level:
- Appeal lifecycle: file → review → evidence → hearing → verdict → enforce
- Temporal windows: time-bounded appeal eligibility
- Witness quorum: independent witness panel for adjudication
- Evidence framework: structured proof submission and verification
- Rollback semantics: T3/V3 restoration with audit trail
- Escalation: multi-level appeals (society → federation)
- Anti-gaming: appeal cost, cooldown, repeat penalties

Spec alignment:
  web4-standard/core-spec/web4-society-authority-law.md
  web4-standard/protocols/web4-witness.md
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── Appeal Types ─────────────────────────────────────────────────────

class AppealType(str, Enum):
    T3_PENALTY = "t3_penalty"           # Trust tensor reduction
    V3_PENALTY = "v3_penalty"           # Value tensor reduction
    CAPABILITY_REVOCATION = "cap_revoke"  # Capability removed
    ROLE_SUSPENSION = "role_suspend"     # Role access suspended
    ATP_SEIZURE = "atp_seizure"         # ATP forcibly deducted
    SOCIETY_EXPULSION = "expulsion"      # Expelled from society


class AppealStatus(str, Enum):
    FILED = "filed"               # Appeal submitted, awaiting review
    UNDER_REVIEW = "under_review"  # Panel assigned, reviewing
    EVIDENCE_PHASE = "evidence"    # Collecting evidence
    HEARING = "hearing"            # Panel hearing in progress
    VERDICT_PENDING = "verdict_pending"  # Panel deliberating
    UPHELD = "upheld"             # Appeal granted (penalty reversed)
    DENIED = "denied"             # Appeal rejected (penalty stands)
    PARTIAL = "partial"           # Partially upheld
    WITHDRAWN = "withdrawn"        # Appellant withdrew
    EXPIRED = "expired"           # Appeal window elapsed


class EvidenceType(str, Enum):
    WITNESS_ATTESTATION = "witness_attestation"
    TRANSACTION_LOG = "transaction_log"
    BEHAVIORAL_RECORD = "behavioral_record"
    CONTEXT_EXPLANATION = "context_explanation"
    THIRD_PARTY_TESTIMONY = "third_party_testimony"
    SYSTEM_MALFUNCTION = "system_malfunction"
    POLICY_INTERPRETATION = "policy_interpretation"


class VerdictType(str, Enum):
    FULL_REVERSAL = "full_reversal"     # Complete penalty rollback
    PARTIAL_REVERSAL = "partial_reversal"  # Reduced penalty
    UPHELD = "upheld"                    # Penalty stands
    MODIFIED = "modified"                # Different penalty applied
    REMANDED = "remanded"                # Sent to higher authority


# ── Data Structures ──────────────────────────────────────────────────

@dataclass
class Penalty:
    """A trust penalty that can be appealed."""
    penalty_id: str
    penalty_type: AppealType
    target_lct: str          # LCT receiving the penalty
    issuing_authority: str   # Who imposed it
    society_id: str
    timestamp: str
    details: Dict[str, Any]  # Type-specific penalty data
    law_hash: str = ""       # Law reference that justified penalty
    action_ref: str = ""     # R6 action that triggered penalty

    def to_dict(self) -> dict:
        return {
            "penalty_id": self.penalty_id,
            "penalty_type": self.penalty_type.value,
            "target_lct": self.target_lct,
            "issuing_authority": self.issuing_authority,
            "society_id": self.society_id,
            "timestamp": self.timestamp,
            "details": self.details,
            "law_hash": self.law_hash,
            "action_ref": self.action_ref,
        }


@dataclass
class Evidence:
    """Evidence submitted in support of an appeal."""
    evidence_id: str
    evidence_type: EvidenceType
    submitter: str           # Who submitted this evidence
    content: Dict[str, Any]
    timestamp: str
    signature: str           # Cryptographic signature
    verified: bool = False

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "submitter": self.submitter,
            "content": self.content,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "verified": self.verified,
        }


@dataclass
class PanelMember:
    """Member of an appeal review panel."""
    lct_id: str
    role: str               # "judge", "witness", "advocate"
    t3_composite: float     # Must meet minimum threshold
    society_id: str
    recused: bool = False

    def qualifies(self, min_t3: float = 0.6) -> bool:
        return self.t3_composite >= min_t3 and not self.recused


@dataclass
class Verdict:
    """Panel verdict on an appeal."""
    verdict_type: VerdictType
    panel_votes: Dict[str, str]  # member_id -> vote
    majority_reached: bool
    reasoning: str
    remedy: Dict[str, Any]      # What to restore/modify
    timestamp: str
    panel_hash: str = ""        # Hash of panel composition

    def to_dict(self) -> dict:
        return {
            "verdict_type": self.verdict_type.value,
            "panel_votes": self.panel_votes,
            "majority_reached": self.majority_reached,
            "reasoning": self.reasoning,
            "remedy": self.remedy,
            "timestamp": self.timestamp,
            "panel_hash": self.panel_hash,
        }


@dataclass
class Appeal:
    """A formal appeal of a trust penalty."""
    appeal_id: str
    penalty: Penalty
    appellant: str           # LCT filing the appeal
    status: AppealStatus
    filed_at: str
    appeal_window_end: str   # Deadline for appeal
    evidence: List[Evidence] = field(default_factory=list)
    panel: List[PanelMember] = field(default_factory=list)
    verdict: Optional[Verdict] = None
    atp_cost: float = 0.0   # Cost to file appeal
    escalation_level: int = 0  # 0=society, 1=federation
    history: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "appeal_id": self.appeal_id,
            "penalty": self.penalty.to_dict(),
            "appellant": self.appellant,
            "status": self.status.value,
            "filed_at": self.filed_at,
            "appeal_window_end": self.appeal_window_end,
            "evidence_count": len(self.evidence),
            "panel_size": len(self.panel),
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "atp_cost": self.atp_cost,
            "escalation_level": self.escalation_level,
        }


# ── Appeal Configuration ─────────────────────────────────────────────

@dataclass
class AppealConfig:
    """Configuration for appeals within a society."""
    appeal_window_seconds: int = 7 * 24 * 3600  # 7 days default
    min_panel_size: int = 3                      # Minimum 3 reviewers
    panel_majority: float = 2/3                   # 2/3 majority
    min_panel_t3: float = 0.6                    # Minimum T3 for panel
    base_atp_cost: float = 5.0                   # Base cost to file
    cost_multiplier_per_level: float = 2.0       # Escalation cost doubles
    max_escalation_levels: int = 2               # Society → Federation → ?
    cooldown_after_denied: int = 30 * 24 * 3600  # 30 days between appeals
    max_evidence_items: int = 10                 # Max evidence per appeal
    max_active_appeals: int = 3                  # Per entity


# ── Appeal Eligibility ───────────────────────────────────────────────

class AppealEligibilityChecker:
    """Check whether an entity can file an appeal."""

    def __init__(self, config: AppealConfig):
        self.config = config

    def check_eligibility(self, penalty: Penalty, appellant_lct: str,
                          current_time: float,
                          active_appeals: int,
                          last_denied_time: Optional[float] = None) -> Tuple[bool, str]:
        """Check if an appeal can be filed."""

        # Window check
        from datetime import datetime, timezone
        try:
            penalty_time = datetime.fromisoformat(
                penalty.timestamp.replace("Z", "+00:00")).timestamp()
        except Exception:
            return False, "Invalid penalty timestamp"

        elapsed = current_time - penalty_time
        if elapsed > self.config.appeal_window_seconds:
            return False, (f"Appeal window expired ({elapsed:.0f}s elapsed, "
                          f"max {self.config.appeal_window_seconds}s)")

        # Can only appeal own penalties
        if penalty.target_lct != appellant_lct:
            return False, "Can only appeal penalties against own LCT"

        # Active appeal limit
        if active_appeals >= self.config.max_active_appeals:
            return False, f"Too many active appeals ({active_appeals}/{self.config.max_active_appeals})"

        # Cooldown after denied
        if last_denied_time is not None:
            cooldown_remaining = (last_denied_time + self.config.cooldown_after_denied) - current_time
            if cooldown_remaining > 0:
                return False, f"Cooldown period: {cooldown_remaining:.0f}s remaining"

        return True, "Eligible"


# ── Panel Selection ──────────────────────────────────────────────────

class PanelSelector:
    """Select an impartial review panel."""

    def __init__(self, config: AppealConfig):
        self.config = config

    def select_panel(self, candidates: List[PanelMember],
                     excluded_lcts: List[str]) -> Tuple[List[PanelMember], List[str]]:
        """Select a panel from candidates, excluding conflicted parties."""
        errors = []

        # Filter out excluded entities (parties to the dispute)
        eligible = [c for c in candidates
                    if c.lct_id not in excluded_lcts
                    and c.qualifies(self.config.min_panel_t3)
                    and not c.recused]

        if len(eligible) < self.config.min_panel_size:
            errors.append(f"Insufficient eligible panelists: "
                         f"{len(eligible)} < {self.config.min_panel_size}")
            return eligible, errors

        # Select top by T3 composite, up to panel size
        eligible.sort(key=lambda m: m.t3_composite, reverse=True)
        panel = eligible[:max(self.config.min_panel_size, len(eligible))]

        # Verify diversity (at least 2 different roles if possible)
        roles = set(m.role for m in panel)
        if len(roles) < 2 and len(panel) >= 2:
            errors.append("Warning: panel lacks role diversity")

        return panel, errors


# ── Voting ───────────────────────────────────────────────────────────

class PanelVoting:
    """Manage panel voting on appeal verdicts."""

    def __init__(self, config: AppealConfig):
        self.config = config

    def tally_votes(self, votes: Dict[str, str],
                    panel: List[PanelMember]) -> Tuple[VerdictType, bool, str]:
        """Tally panel votes and determine verdict.

        Votes: "upheld" (reverse penalty), "denied" (keep penalty),
               "partial" (reduce penalty), "abstain"
        """
        # Count by verdict preference
        counts = {"upheld": 0, "denied": 0, "partial": 0, "abstain": 0}
        for member_id, vote in votes.items():
            if vote in counts:
                counts[vote] += 1

        total_non_abstain = sum(v for k, v in counts.items() if k != "abstain")
        if total_non_abstain == 0:
            return VerdictType.UPHELD, False, "No non-abstain votes"

        # Check for majority
        threshold = total_non_abstain * self.config.panel_majority

        if counts["upheld"] >= threshold:
            return VerdictType.FULL_REVERSAL, True, \
                f"Upheld with {counts['upheld']}/{total_non_abstain} votes"
        elif counts["denied"] >= threshold:
            return VerdictType.UPHELD, True, \
                f"Denied with {counts['denied']}/{total_non_abstain} votes"
        elif counts["partial"] >= threshold:
            return VerdictType.PARTIAL_REVERSAL, True, \
                f"Partial reversal with {counts['partial']}/{total_non_abstain} votes"
        else:
            # No majority — most common vote wins (simple majority fallback)
            top_vote = max(counts.items(), key=lambda x: x[1] if x[0] != "abstain" else -1)
            verdict_map = {
                "upheld": VerdictType.FULL_REVERSAL,
                "denied": VerdictType.UPHELD,
                "partial": VerdictType.PARTIAL_REVERSAL,
            }
            return verdict_map.get(top_vote[0], VerdictType.UPHELD), False, \
                f"No supermajority, plurality: {top_vote[0]} ({top_vote[1]}/{total_non_abstain})"


# ── T3/V3 Rollback ──────────────────────────────────────────────────

@dataclass
class TensorSnapshot:
    """Point-in-time tensor values for rollback."""
    talent: float
    training: float
    temperament: float
    t3_composite: float
    valuation: float = 0.0
    veracity: float = 0.5
    validity: float = 0.5
    v3_composite: float = 0.35
    timestamp: str = ""


class TensorRollback:
    """Manage T3/V3 rollback on appeal success."""

    def __init__(self):
        self._snapshots: Dict[str, List[TensorSnapshot]] = {}

    def save_snapshot(self, lct_id: str, snapshot: TensorSnapshot):
        if lct_id not in self._snapshots:
            self._snapshots[lct_id] = []
        self._snapshots[lct_id].append(snapshot)

    def get_snapshot_before(self, lct_id: str, timestamp: str) -> Optional[TensorSnapshot]:
        """Get the most recent snapshot before a given timestamp."""
        if lct_id not in self._snapshots:
            return None
        candidates = [s for s in self._snapshots[lct_id] if s.timestamp < timestamp]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.timestamp)

    def compute_remedy(self, current: TensorSnapshot,
                       pre_penalty: TensorSnapshot,
                       verdict: VerdictType) -> Dict[str, Any]:
        """Compute the tensor adjustment for a verdict."""
        if verdict == VerdictType.FULL_REVERSAL:
            # Full restoration to pre-penalty values
            return {
                "talent_delta": pre_penalty.talent - current.talent,
                "training_delta": pre_penalty.training - current.training,
                "temperament_delta": pre_penalty.temperament - current.temperament,
                "valuation_delta": pre_penalty.valuation - current.valuation,
                "veracity_delta": pre_penalty.veracity - current.veracity,
                "validity_delta": pre_penalty.validity - current.validity,
                "restore_type": "full",
            }
        elif verdict == VerdictType.PARTIAL_REVERSAL:
            # Restore 50% of the difference
            return {
                "talent_delta": (pre_penalty.talent - current.talent) * 0.5,
                "training_delta": (pre_penalty.training - current.training) * 0.5,
                "temperament_delta": (pre_penalty.temperament - current.temperament) * 0.5,
                "valuation_delta": (pre_penalty.valuation - current.valuation) * 0.5,
                "veracity_delta": (pre_penalty.veracity - current.veracity) * 0.5,
                "validity_delta": (pre_penalty.validity - current.validity) * 0.5,
                "restore_type": "partial_50pct",
            }
        else:
            return {
                "talent_delta": 0, "training_delta": 0, "temperament_delta": 0,
                "valuation_delta": 0, "veracity_delta": 0, "validity_delta": 0,
                "restore_type": "none",
            }


# ── Appeal Manager ───────────────────────────────────────────────────

class AppealManager:
    """Orchestrates the full appeal lifecycle."""

    def __init__(self, config: Optional[AppealConfig] = None):
        self.config = config or AppealConfig()
        self.eligibility = AppealEligibilityChecker(self.config)
        self.panel_selector = PanelSelector(self.config)
        self.voting = PanelVoting(self.config)
        self.rollback = TensorRollback()
        self._appeals: Dict[str, Appeal] = {}
        self._denied_times: Dict[str, float] = {}
        self._audit_log: List[dict] = []

    def _now_iso(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _log(self, event: str, appeal_id: str, details: dict):
        self._audit_log.append({
            "event": event,
            "appeal_id": appeal_id,
            "details": details,
            "ts": self._now_iso(),
        })

    def file_appeal(self, penalty: Penalty, appellant: str,
                    atp_balance: float) -> Tuple[Optional[Appeal], str]:
        """File a new appeal."""
        # Check eligibility
        active = sum(1 for a in self._appeals.values()
                     if a.appellant == appellant
                     and a.status in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW,
                                      AppealStatus.EVIDENCE_PHASE, AppealStatus.HEARING,
                                      AppealStatus.VERDICT_PENDING))
        last_denied = self._denied_times.get(appellant)

        ok, reason = self.eligibility.check_eligibility(
            penalty, appellant, time.time(), active, last_denied
        )
        if not ok:
            return None, reason

        # Check ATP cost
        cost = self.config.base_atp_cost * (self.config.cost_multiplier_per_level ** 0)
        if atp_balance < cost:
            return None, f"Insufficient ATP: {atp_balance} < {cost}"

        # Create appeal
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(seconds=self.config.appeal_window_seconds)

        appeal_id = f"appeal:{hashlib.sha256(f'{penalty.penalty_id}:{appellant}:{time.time()}'.encode()).hexdigest()[:16]}"
        appeal = Appeal(
            appeal_id=appeal_id,
            penalty=penalty,
            appellant=appellant,
            status=AppealStatus.FILED,
            filed_at=now.isoformat().replace("+00:00", "Z"),
            appeal_window_end=window_end.isoformat().replace("+00:00", "Z"),
            atp_cost=cost,
        )
        appeal.history.append({"event": "filed", "ts": appeal.filed_at})
        self._appeals[appeal_id] = appeal
        self._log("appeal_filed", appeal_id, {"penalty_id": penalty.penalty_id})
        return appeal, "Appeal filed successfully"

    def submit_evidence(self, appeal_id: str, evidence: Evidence) -> Tuple[bool, str]:
        """Submit evidence for an appeal."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found"
        if appeal.status not in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW,
                                  AppealStatus.EVIDENCE_PHASE):
            return False, f"Cannot submit evidence in status {appeal.status.value}"
        if len(appeal.evidence) >= self.config.max_evidence_items:
            return False, f"Maximum evidence items reached ({self.config.max_evidence_items})"

        appeal.evidence.append(evidence)
        appeal.history.append({
            "event": "evidence_submitted",
            "evidence_id": evidence.evidence_id,
            "ts": self._now_iso(),
        })
        self._log("evidence_submitted", appeal_id,
                  {"evidence_id": evidence.evidence_id, "type": evidence.evidence_type.value})
        return True, "Evidence accepted"

    def assign_panel(self, appeal_id: str,
                     candidates: List[PanelMember]) -> Tuple[bool, str]:
        """Assign a review panel to an appeal."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found"
        if appeal.status not in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW):
            return False, f"Cannot assign panel in status {appeal.status.value}"

        # Exclude conflicted parties
        excluded = [appeal.appellant, appeal.penalty.issuing_authority]
        panel, errors = self.panel_selector.select_panel(candidates, excluded)

        if len(panel) < self.config.min_panel_size:
            return False, f"Insufficient panelists: {errors}"

        appeal.panel = panel
        appeal.status = AppealStatus.UNDER_REVIEW
        appeal.history.append({
            "event": "panel_assigned",
            "panel_size": len(panel),
            "ts": self._now_iso(),
        })
        self._log("panel_assigned", appeal_id,
                  {"panel_size": len(panel), "members": [m.lct_id for m in panel]})
        return True, f"Panel of {len(panel)} assigned"

    def start_hearing(self, appeal_id: str) -> Tuple[bool, str]:
        """Move appeal to hearing phase."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found"
        if appeal.status != AppealStatus.UNDER_REVIEW:
            return False, f"Cannot start hearing from status {appeal.status.value}"
        if not appeal.panel:
            return False, "No panel assigned"

        appeal.status = AppealStatus.HEARING
        appeal.history.append({"event": "hearing_started", "ts": self._now_iso()})
        self._log("hearing_started", appeal_id, {})
        return True, "Hearing started"

    def submit_votes(self, appeal_id: str,
                     votes: Dict[str, str]) -> Tuple[Optional[Verdict], str]:
        """Submit panel votes and generate verdict."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return None, "Appeal not found"
        if appeal.status != AppealStatus.HEARING:
            return None, f"Cannot vote in status {appeal.status.value}"

        # Validate voters are on panel
        panel_ids = {m.lct_id for m in appeal.panel}
        for voter in votes:
            if voter not in panel_ids:
                return None, f"Voter {voter} not on panel"

        # Tally votes
        verdict_type, majority, reasoning = self.voting.tally_votes(votes, appeal.panel)

        # Compute remedy
        remedy = {}
        if verdict_type in (VerdictType.FULL_REVERSAL, VerdictType.PARTIAL_REVERSAL):
            pre_snapshot = self.rollback.get_snapshot_before(
                appeal.penalty.target_lct, appeal.penalty.timestamp
            )
            if pre_snapshot:
                current = TensorSnapshot(
                    talent=appeal.penalty.details.get("current_talent", 0.5),
                    training=appeal.penalty.details.get("current_training", 0.5),
                    temperament=appeal.penalty.details.get("current_temperament", 0.5),
                    t3_composite=appeal.penalty.details.get("current_t3", 0.5),
                )
                remedy = self.rollback.compute_remedy(current, pre_snapshot, verdict_type)

        # Compute panel hash
        panel_hash = hashlib.sha256(
            json.dumps(sorted([m.lct_id for m in appeal.panel])).encode()
        ).hexdigest()[:16]

        verdict = Verdict(
            verdict_type=verdict_type,
            panel_votes=votes,
            majority_reached=majority,
            reasoning=reasoning,
            remedy=remedy,
            timestamp=self._now_iso(),
            panel_hash=panel_hash,
        )

        appeal.verdict = verdict

        # Update status based on verdict
        if verdict_type == VerdictType.FULL_REVERSAL:
            appeal.status = AppealStatus.UPHELD
        elif verdict_type == VerdictType.PARTIAL_REVERSAL:
            appeal.status = AppealStatus.PARTIAL
        elif verdict_type == VerdictType.UPHELD:
            appeal.status = AppealStatus.DENIED
            self._denied_times[appeal.appellant] = time.time()
        elif verdict_type == VerdictType.REMANDED:
            appeal.status = AppealStatus.UNDER_REVIEW
            appeal.escalation_level += 1

        appeal.history.append({
            "event": "verdict_rendered",
            "verdict": verdict_type.value,
            "majority": majority,
            "ts": self._now_iso(),
        })
        self._log("verdict_rendered", appeal_id, verdict.to_dict())
        return verdict, reasoning

    def withdraw_appeal(self, appeal_id: str, appellant: str) -> Tuple[bool, str]:
        """Withdraw an appeal."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return False, "Appeal not found"
        if appeal.appellant != appellant:
            return False, "Only appellant can withdraw"
        if appeal.status in (AppealStatus.UPHELD, AppealStatus.DENIED,
                             AppealStatus.PARTIAL, AppealStatus.EXPIRED):
            return False, f"Cannot withdraw in status {appeal.status.value}"

        appeal.status = AppealStatus.WITHDRAWN
        appeal.history.append({"event": "withdrawn", "ts": self._now_iso()})
        self._log("appeal_withdrawn", appeal_id, {})
        return True, "Appeal withdrawn"

    def get_appeal(self, appeal_id: str) -> Optional[Appeal]:
        return self._appeals.get(appeal_id)

    def get_audit_log(self) -> List[dict]:
        return list(self._audit_log)

    def get_active_appeals(self, appellant: str) -> List[Appeal]:
        return [a for a in self._appeals.values()
                if a.appellant == appellant
                and a.status in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW,
                                 AppealStatus.EVIDENCE_PHASE, AppealStatus.HEARING,
                                 AppealStatus.VERDICT_PENDING)]


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    from datetime import datetime, timezone, timedelta

    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat().replace("+00:00", "Z")
    recent_iso = (now - timedelta(minutes=30)).isoformat().replace("+00:00", "Z")

    # ── T1: Appeal Types ─────────────────────────────────────────
    print("T1: Appeal Types")
    check("T1.1 Six appeal types", len(AppealType) == 6)
    check("T1.2 T3_PENALTY exists", AppealType.T3_PENALTY.value == "t3_penalty")
    check("T1.3 V3_PENALTY exists", AppealType.V3_PENALTY.value == "v3_penalty")
    check("T1.4 EXPULSION exists", AppealType.SOCIETY_EXPULSION.value == "expulsion")

    # ── T2: Appeal Status Lifecycle ──────────────────────────────
    print("T2: Appeal Status Lifecycle")
    check("T2.1 Ten status values", len(AppealStatus) == 10)
    check("T2.2 FILED status", AppealStatus.FILED.value == "filed")
    check("T2.3 UPHELD status", AppealStatus.UPHELD.value == "upheld")
    check("T2.4 DENIED status", AppealStatus.DENIED.value == "denied")
    check("T2.5 EXPIRED status", AppealStatus.EXPIRED.value == "expired")
    check("T2.6 WITHDRAWN status", AppealStatus.WITHDRAWN.value == "withdrawn")

    # ── T3: Evidence Types ───────────────────────────────────────
    print("T3: Evidence Types")
    check("T3.1 Seven evidence types", len(EvidenceType) == 7)
    check("T3.2 Witness attestation", EvidenceType.WITNESS_ATTESTATION.value == "witness_attestation")
    check("T3.3 System malfunction", EvidenceType.SYSTEM_MALFUNCTION.value == "system_malfunction")
    check("T3.4 Policy interpretation", EvidenceType.POLICY_INTERPRETATION.value == "policy_interpretation")

    # ── T4: Penalty Structure ────────────────────────────────────
    print("T4: Penalty Structure")
    penalty = Penalty(
        penalty_id="pen:abc123",
        penalty_type=AppealType.T3_PENALTY,
        target_lct="lct:web4:ai:agent-1",
        issuing_authority="lct:web4:oracle:auditor-1",
        society_id="lct:web4:society:acme",
        timestamp=recent_iso,
        details={"talent_delta": -0.1, "current_talent": 0.4, "current_training": 0.5,
                 "current_temperament": 0.5, "current_t3": 0.45},
        law_hash="sha256:law123",
        action_ref="r6:action:456",
    )
    d = penalty.to_dict()
    check("T4.1 Penalty serializable", "penalty_id" in d)
    check("T4.2 Has penalty_type", d["penalty_type"] == "t3_penalty")
    check("T4.3 Has target_lct", d["target_lct"] == "lct:web4:ai:agent-1")
    check("T4.4 Has law_hash", d["law_hash"] == "sha256:law123")

    # ── T5: Eligibility Checks ───────────────────────────────────
    print("T5: Eligibility Checks")
    config = AppealConfig(appeal_window_seconds=3600)  # 1 hour for testing
    checker = AppealEligibilityChecker(config)

    ok, reason = checker.check_eligibility(penalty, "lct:web4:ai:agent-1",
                                            time.time(), 0)
    check("T5.1 Eligible for recent penalty", ok)

    # Expired window
    old_penalty = Penalty(
        penalty_id="pen:old",
        penalty_type=AppealType.T3_PENALTY,
        target_lct="lct:web4:ai:agent-1",
        issuing_authority="lct:web4:oracle:auditor-1",
        society_id="lct:web4:society:acme",
        timestamp="2020-01-01T00:00:00Z",
        details={},
    )
    ok, reason = checker.check_eligibility(old_penalty, "lct:web4:ai:agent-1",
                                            time.time(), 0)
    check("T5.2 Expired window rejected", not ok)
    check("T5.3 Reason mentions window", "window" in reason.lower() or "expired" in reason.lower())

    # Wrong appellant
    ok, reason = checker.check_eligibility(penalty, "lct:web4:ai:other",
                                            time.time(), 0)
    check("T5.4 Wrong appellant rejected", not ok)

    # Too many active appeals
    ok, reason = checker.check_eligibility(penalty, "lct:web4:ai:agent-1",
                                            time.time(), 5)
    check("T5.5 Too many active appeals rejected", not ok)

    # Cooldown period (use a fresh penalty so window check doesn't trigger first)
    fresh_penalty = Penalty(
        penalty_id="pen:cooldown",
        penalty_type=AppealType.T3_PENALTY,
        target_lct="lct:web4:ai:agent-1",
        issuing_authority="lct:web4:oracle:auditor-1",
        society_id="lct:web4:society:acme",
        timestamp=now_iso,
        details={},
    )
    ok, reason = checker.check_eligibility(fresh_penalty, "lct:web4:ai:agent-1",
                                            time.time(), 0,
                                            last_denied_time=time.time() - 60)
    check("T5.6 Cooldown period enforced", not ok)
    check("T5.7 Cooldown reason mentions remaining", "remaining" in reason.lower())

    # ── T6: Panel Selection ──────────────────────────────────────
    print("T6: Panel Selection")
    selector = PanelSelector(config)
    candidates = [
        PanelMember("lct:web4:human:judge1", "judge", 0.8, "soc1"),
        PanelMember("lct:web4:human:judge2", "judge", 0.7, "soc1"),
        PanelMember("lct:web4:oracle:witness1", "witness", 0.9, "soc1"),
        PanelMember("lct:web4:human:judge3", "judge", 0.5, "soc1"),  # Below threshold
        PanelMember("lct:web4:ai:agent-1", "judge", 0.85, "soc1"),  # Conflicted
    ]

    panel, errors = selector.select_panel(candidates,
                                           excluded_lcts=["lct:web4:ai:agent-1",
                                                          "lct:web4:oracle:auditor-1"])
    check("T6.1 Panel selected", len(panel) >= 3)
    check("T6.2 Conflicted party excluded",
          "lct:web4:ai:agent-1" not in [m.lct_id for m in panel])
    check("T6.3 Low-T3 excluded",
          "lct:web4:human:judge3" not in [m.lct_id for m in panel])
    check("T6.4 Sorted by T3 (highest first)", panel[0].t3_composite >= panel[1].t3_composite)

    # Insufficient candidates
    panel2, errors2 = selector.select_panel(
        [PanelMember("lct:web4:human:solo", "judge", 0.8, "soc1")],
        excluded_lcts=[]
    )
    check("T6.5 Insufficient candidates error", len(errors2) > 0)

    # Recused member excluded
    recused = PanelMember("lct:web4:human:recused", "judge", 0.95, "soc1", recused=True)
    check("T6.6 Recused member doesn't qualify", not recused.qualifies())

    # ── T7: Panel Voting ─────────────────────────────────────────
    print("T7: Panel Voting")
    voting = PanelVoting(config)

    # Unanimous upheld
    votes_upheld = {"j1": "upheld", "j2": "upheld", "j3": "upheld"}
    vtype, majority, reason = voting.tally_votes(votes_upheld, panel)
    check("T7.1 Unanimous upheld = FULL_REVERSAL", vtype == VerdictType.FULL_REVERSAL)
    check("T7.2 Majority reached", majority)

    # Unanimous denied
    votes_denied = {"j1": "denied", "j2": "denied", "j3": "denied"}
    vtype, majority, reason = voting.tally_votes(votes_denied, panel)
    check("T7.3 Unanimous denied = UPHELD (penalty)", vtype == VerdictType.UPHELD)
    check("T7.4 Majority reached", majority)

    # 2/3 partial
    votes_partial = {"j1": "partial", "j2": "partial", "j3": "denied"}
    vtype, majority, reason = voting.tally_votes(votes_partial, panel)
    check("T7.5 2/3 partial = PARTIAL_REVERSAL", vtype == VerdictType.PARTIAL_REVERSAL)
    check("T7.6 Majority reached", majority)

    # Split vote (no supermajority)
    votes_split = {"j1": "upheld", "j2": "denied", "j3": "partial"}
    vtype, majority, reason = voting.tally_votes(votes_split, panel)
    check("T7.7 Split vote = no majority", not majority)

    # All abstain
    votes_abstain = {"j1": "abstain", "j2": "abstain", "j3": "abstain"}
    vtype, majority, reason = voting.tally_votes(votes_abstain, panel)
    check("T7.8 All abstain = UPHELD (default)", vtype == VerdictType.UPHELD)
    check("T7.9 No majority on abstain", not majority)

    # ── T8: Tensor Rollback ──────────────────────────────────────
    print("T8: Tensor Rollback")
    rollback = TensorRollback()

    pre = TensorSnapshot(
        talent=0.8, training=0.7, temperament=0.9, t3_composite=0.8,
        valuation=0.5, veracity=0.8, validity=0.7, v3_composite=0.67,
        timestamp="2026-02-19T00:00:00Z",
    )
    rollback.save_snapshot("lct:web4:ai:agent-1", pre)

    current = TensorSnapshot(
        talent=0.4, training=0.5, temperament=0.5, t3_composite=0.45,
    )

    # Full reversal
    remedy = rollback.compute_remedy(current, pre, VerdictType.FULL_REVERSAL)
    check("T8.1 Full reversal: talent delta = 0.4",
          abs(remedy["talent_delta"] - 0.4) < 0.001)
    check("T8.2 Full reversal: training delta = 0.2",
          abs(remedy["training_delta"] - 0.2) < 0.001)
    check("T8.3 Full reversal restore_type", remedy["restore_type"] == "full")

    # Partial reversal (50%)
    remedy_p = rollback.compute_remedy(current, pre, VerdictType.PARTIAL_REVERSAL)
    check("T8.4 Partial: talent delta = 0.2",
          abs(remedy_p["talent_delta"] - 0.2) < 0.001)
    check("T8.5 Partial restore_type", remedy_p["restore_type"] == "partial_50pct")

    # No reversal
    remedy_n = rollback.compute_remedy(current, pre, VerdictType.UPHELD)
    check("T8.6 No reversal: all deltas = 0",
          all(remedy_n[f"{d}_delta"] == 0 for d in ["talent", "training", "temperament"]))
    check("T8.7 No reversal restore_type", remedy_n["restore_type"] == "none")

    # Snapshot retrieval
    snap = rollback.get_snapshot_before("lct:web4:ai:agent-1", "2026-12-31T00:00:00Z")
    check("T8.8 Snapshot retrieved", snap is not None)
    check("T8.9 Snapshot has correct talent", snap.talent == 0.8)

    snap_none = rollback.get_snapshot_before("lct:web4:unknown", "2026-12-31T00:00:00Z")
    check("T8.10 Unknown entity returns None", snap_none is None)

    # ── T9: Full Appeal Lifecycle ────────────────────────────────
    print("T9: Full Appeal Lifecycle")
    mgr = AppealManager(AppealConfig(appeal_window_seconds=3600))

    # Save pre-penalty snapshot
    mgr.rollback.save_snapshot("lct:web4:ai:agent-1", pre)

    # File appeal
    appeal, msg = mgr.file_appeal(penalty, "lct:web4:ai:agent-1", atp_balance=100.0)
    check("T9.1 Appeal filed", appeal is not None)
    check("T9.2 Status is FILED", appeal.status == AppealStatus.FILED)
    check("T9.3 ATP cost set", appeal.atp_cost == 5.0)

    # Submit evidence
    ev = Evidence(
        evidence_id="ev:001",
        evidence_type=EvidenceType.CONTEXT_EXPLANATION,
        submitter="lct:web4:ai:agent-1",
        content={"explanation": "The action was taken under emergency policy override"},
        timestamp=now_iso,
        signature="cose:ev_sig_001",
    )
    ok, msg = mgr.submit_evidence(appeal.appeal_id, ev)
    check("T9.4 Evidence submitted", ok)
    check("T9.5 Evidence recorded", len(appeal.evidence) == 1)

    # Assign panel
    ok, msg = mgr.assign_panel(appeal.appeal_id, candidates)
    check("T9.6 Panel assigned", ok)
    check("T9.7 Status is UNDER_REVIEW", appeal.status == AppealStatus.UNDER_REVIEW)
    check("T9.8 Panel has members", len(appeal.panel) >= 3)

    # Start hearing
    ok, msg = mgr.start_hearing(appeal.appeal_id)
    check("T9.9 Hearing started", ok)
    check("T9.10 Status is HEARING", appeal.status == AppealStatus.HEARING)

    # Submit votes (2/3 upheld)
    panel_ids = [m.lct_id for m in appeal.panel]
    votes = {panel_ids[0]: "upheld", panel_ids[1]: "upheld", panel_ids[2]: "denied"}
    verdict, reason = mgr.submit_votes(appeal.appeal_id, votes)
    check("T9.11 Verdict rendered", verdict is not None)
    check("T9.12 FULL_REVERSAL", verdict.verdict_type == VerdictType.FULL_REVERSAL)
    check("T9.13 Majority reached", verdict.majority_reached)
    check("T9.14 Status is UPHELD", appeal.status == AppealStatus.UPHELD)
    check("T9.15 Remedy has talent_delta", "talent_delta" in verdict.remedy)
    check("T9.16 Panel hash set", len(verdict.panel_hash) == 16)

    # History recorded
    check("T9.17 History has events", len(appeal.history) >= 4)
    check("T9.18 First event is filed", appeal.history[0]["event"] == "filed")

    # Audit log
    log = mgr.get_audit_log()
    check("T9.19 Audit log has entries", len(log) >= 3)

    # ── T10: Appeal Denial Lifecycle ─────────────────────────────
    print("T10: Appeal Denial Lifecycle")
    penalty2 = Penalty(
        penalty_id="pen:deny-test",
        penalty_type=AppealType.CAPABILITY_REVOCATION,
        target_lct="lct:web4:ai:agent-2",
        issuing_authority="lct:web4:oracle:auditor-2",
        society_id="lct:web4:society:acme",
        timestamp=recent_iso,
        details={},
    )

    mgr2 = AppealManager(AppealConfig(appeal_window_seconds=3600))
    appeal2, _ = mgr2.file_appeal(penalty2, "lct:web4:ai:agent-2", 100.0)
    check("T10.1 Appeal filed", appeal2 is not None)

    mgr2.assign_panel(appeal2.appeal_id, candidates)
    mgr2.start_hearing(appeal2.appeal_id)

    # Unanimous denial
    panel_ids2 = [m.lct_id for m in appeal2.panel]
    votes2 = {pid: "denied" for pid in panel_ids2}
    verdict2, _ = mgr2.submit_votes(appeal2.appeal_id, votes2)
    check("T10.2 Verdict is UPHELD (denied)", verdict2.verdict_type == VerdictType.UPHELD)
    check("T10.3 Status is DENIED", appeal2.status == AppealStatus.DENIED)

    # Cooldown enforcement
    penalty3 = Penalty(
        penalty_id="pen:cooldown-test",
        penalty_type=AppealType.T3_PENALTY,
        target_lct="lct:web4:ai:agent-2",
        issuing_authority="lct:web4:oracle:auditor-2",
        society_id="lct:web4:society:acme",
        timestamp=recent_iso,
        details={},
    )
    appeal3, msg3 = mgr2.file_appeal(penalty3, "lct:web4:ai:agent-2", 100.0)
    check("T10.4 Cooldown prevents re-appeal", appeal3 is None)
    check("T10.5 Cooldown reason", "cooldown" in msg3.lower())

    # ── T11: Appeal Withdrawal ───────────────────────────────────
    print("T11: Appeal Withdrawal")
    penalty4 = Penalty(
        penalty_id="pen:withdraw",
        penalty_type=AppealType.V3_PENALTY,
        target_lct="lct:web4:ai:agent-3",
        issuing_authority="lct:web4:oracle:auditor-3",
        society_id="lct:web4:society:acme",
        timestamp=recent_iso,
        details={},
    )
    mgr3 = AppealManager(AppealConfig(appeal_window_seconds=3600))
    appeal4, _ = mgr3.file_appeal(penalty4, "lct:web4:ai:agent-3", 100.0)

    ok, _ = mgr3.withdraw_appeal(appeal4.appeal_id, "lct:web4:ai:agent-3")
    check("T11.1 Withdrawal succeeds", ok)
    check("T11.2 Status is WITHDRAWN", appeal4.status == AppealStatus.WITHDRAWN)

    # Cannot withdraw someone else's appeal
    ok, msg = mgr3.withdraw_appeal(appeal4.appeal_id, "lct:web4:ai:other")
    check("T11.3 Wrong appellant rejected", not ok)

    # ── T12: Insufficient ATP ────────────────────────────────────
    print("T12: Insufficient ATP")
    mgr4 = AppealManager()
    appeal5, msg5 = mgr4.file_appeal(penalty, "lct:web4:ai:agent-1", atp_balance=1.0)
    check("T12.1 Insufficient ATP rejected", appeal5 is None)
    check("T12.2 Reason mentions ATP", "atp" in msg5.lower())

    # ── T13: Evidence Limits ─────────────────────────────────────
    print("T13: Evidence Limits")
    mgr5 = AppealManager(AppealConfig(appeal_window_seconds=3600, max_evidence_items=2))
    appeal6, _ = mgr5.file_appeal(penalty, "lct:web4:ai:agent-1", 100.0)

    for i in range(2):
        ev = Evidence(f"ev:{i}", EvidenceType.TRANSACTION_LOG, "lct:web4:ai:agent-1",
                      {"data": f"log-{i}"}, now_iso, f"sig-{i}")
        ok, _ = mgr5.submit_evidence(appeal6.appeal_id, ev)
        check(f"T13.{i+1} Evidence {i} accepted", ok)

    ev_extra = Evidence("ev:extra", EvidenceType.TRANSACTION_LOG, "lct:web4:ai:agent-1",
                        {"data": "extra"}, now_iso, "sig-extra")
    ok, msg = mgr5.submit_evidence(appeal6.appeal_id, ev_extra)
    check("T13.3 Third evidence rejected (max 2)", not ok)
    check("T13.4 Reason mentions maximum", "maximum" in msg.lower())

    # ── T14: Active Appeals Limit ────────────────────────────────
    print("T14: Active Appeals Limit")
    config_limited = AppealConfig(appeal_window_seconds=3600, max_active_appeals=1)
    mgr6 = AppealManager(config_limited)

    pen_a = Penalty("pen:a", AppealType.T3_PENALTY, "lct:web4:ai:limited",
                    "lct:web4:oracle:a", "soc1", recent_iso, {})
    appeal_a, _ = mgr6.file_appeal(pen_a, "lct:web4:ai:limited", 100.0)
    check("T14.1 First appeal filed", appeal_a is not None)

    pen_b = Penalty("pen:b", AppealType.V3_PENALTY, "lct:web4:ai:limited",
                    "lct:web4:oracle:b", "soc1", recent_iso, {})
    appeal_b, msg_b = mgr6.file_appeal(pen_b, "lct:web4:ai:limited", 100.0)
    check("T14.2 Second appeal rejected (max 1)", appeal_b is None)
    check("T14.3 Reason mentions active", "active" in msg_b.lower() or "many" in msg_b.lower())

    # ── T15: Verdict Serialization ───────────────────────────────
    print("T15: Verdict Serialization")
    verdict = Verdict(
        verdict_type=VerdictType.FULL_REVERSAL,
        panel_votes={"j1": "upheld", "j2": "upheld", "j3": "denied"},
        majority_reached=True,
        reasoning="Evidence shows system malfunction caused false positive",
        remedy={"talent_delta": 0.4, "restore_type": "full"},
        timestamp=now_iso,
        panel_hash="abc123def456",
    )
    d = verdict.to_dict()
    check("T15.1 Verdict serializable", "verdict_type" in d)
    check("T15.2 Has panel_votes", len(d["panel_votes"]) == 3)
    check("T15.3 Has majority_reached", d["majority_reached"] is True)
    check("T15.4 Has reasoning", len(d["reasoning"]) > 0)
    check("T15.5 Has remedy", "talent_delta" in d["remedy"])
    check("T15.6 Has panel_hash", d["panel_hash"] == "abc123def456")

    # ── T16: Appeal Serialization ────────────────────────────────
    print("T16: Appeal Serialization")
    test_appeal = mgr.get_appeal(appeal.appeal_id)
    d = test_appeal.to_dict()
    check("T16.1 Appeal serializable", "appeal_id" in d)
    check("T16.2 Has penalty", "penalty" in d)
    check("T16.3 Has status", d["status"] == "upheld")
    check("T16.4 Has evidence_count", d["evidence_count"] == 1)
    check("T16.5 Has panel_size", d["panel_size"] >= 3)
    check("T16.6 Has verdict", d["verdict"] is not None)

    # ── T17: Evidence Structure ──────────────────────────────────
    print("T17: Evidence Structure")
    evidence = Evidence(
        evidence_id="ev:test",
        evidence_type=EvidenceType.SYSTEM_MALFUNCTION,
        submitter="lct:web4:ai:agent-1",
        content={"error_log": "NullPointerException at line 42",
                 "affected_component": "trust_computation"},
        timestamp=now_iso,
        signature="cose:ev_test_sig",
        verified=True,
    )
    d = evidence.to_dict()
    check("T17.1 Evidence serializable", "evidence_id" in d)
    check("T17.2 Has evidence_type", d["evidence_type"] == "system_malfunction")
    check("T17.3 Has content", "error_log" in d["content"])
    check("T17.4 Has verified flag", d["verified"] is True)
    check("T17.5 Has signature", d["signature"].startswith("cose:"))

    # ── T18: Config Customization ────────────────────────────────
    print("T18: Config Customization")
    custom = AppealConfig(
        appeal_window_seconds=14 * 24 * 3600,  # 14 days
        min_panel_size=5,
        panel_majority=0.8,
        base_atp_cost=10.0,
        max_escalation_levels=3,
    )
    check("T18.1 Custom window", custom.appeal_window_seconds == 14 * 24 * 3600)
    check("T18.2 Custom panel size", custom.min_panel_size == 5)
    check("T18.3 Custom majority", custom.panel_majority == 0.8)
    check("T18.4 Custom ATP cost", custom.base_atp_cost == 10.0)
    check("T18.5 Custom escalation levels", custom.max_escalation_levels == 3)

    # ── T19: Edge Cases ──────────────────────────────────────────
    print("T19: Edge Cases")

    # Submit evidence to non-existent appeal
    ok, msg = mgr.submit_evidence("appeal:nonexistent", ev)
    check("T19.1 Evidence to nonexistent appeal rejected", not ok)

    # Assign panel to non-existent appeal
    ok, msg = mgr.assign_panel("appeal:nonexistent", candidates)
    check("T19.2 Panel to nonexistent appeal rejected", not ok)

    # Start hearing without panel
    penalty_np = Penalty("pen:nopanel", AppealType.T3_PENALTY, "lct:web4:ai:np",
                         "lct:web4:oracle:np", "soc1", recent_iso, {})
    mgr_np = AppealManager(AppealConfig(appeal_window_seconds=3600))
    appeal_np, _ = mgr_np.file_appeal(penalty_np, "lct:web4:ai:np", 100.0)
    # Status is FILED, not UNDER_REVIEW → can't start hearing
    ok, msg = mgr_np.start_hearing(appeal_np.appeal_id)
    check("T19.3 Hearing without UNDER_REVIEW status rejected", not ok)

    # Vote on non-hearing appeal
    verdict_bad, msg = mgr_np.submit_votes(appeal_np.appeal_id, {"j1": "upheld"})
    check("T19.4 Vote on non-hearing rejected", verdict_bad is None)

    # Non-panel voter
    mgr_np.assign_panel(appeal_np.appeal_id, candidates)
    mgr_np.start_hearing(appeal_np.appeal_id)
    verdict_bad2, msg = mgr_np.submit_votes(appeal_np.appeal_id,
                                             {"lct:web4:ai:impostor": "upheld"})
    check("T19.5 Non-panel voter rejected", verdict_bad2 is None)

    # Get active appeals for entity with no appeals
    active = mgr.get_active_appeals("lct:web4:ai:noone")
    check("T19.6 No active appeals for unknown entity", len(active) == 0)

    # PanelMember qualification
    pm = PanelMember("lct:web4:human:test", "judge", 0.59, "soc1")
    check("T19.7 Below threshold doesn't qualify", not pm.qualifies(0.6))
    pm2 = PanelMember("lct:web4:human:test2", "judge", 0.6, "soc1")
    check("T19.8 At threshold qualifies", pm2.qualifies(0.6))

    # ── T20: Partial Reversal Lifecycle ──────────────────────────
    print("T20: Partial Reversal Lifecycle")
    mgr7 = AppealManager(AppealConfig(appeal_window_seconds=3600))
    mgr7.rollback.save_snapshot("lct:web4:ai:partial", TensorSnapshot(
        talent=0.9, training=0.8, temperament=0.85, t3_composite=0.86,
        timestamp="2026-02-18T00:00:00Z",
    ))
    pen_partial = Penalty(
        "pen:partial", AppealType.T3_PENALTY, "lct:web4:ai:partial",
        "lct:web4:oracle:p", "soc1", recent_iso,
        {"current_talent": 0.5, "current_training": 0.5,
         "current_temperament": 0.5, "current_t3": 0.5},
    )
    ap, _ = mgr7.file_appeal(pen_partial, "lct:web4:ai:partial", 100.0)
    mgr7.assign_panel(ap.appeal_id, candidates)
    mgr7.start_hearing(ap.appeal_id)

    panel_ids = [m.lct_id for m in ap.panel]
    votes = {panel_ids[0]: "partial", panel_ids[1]: "partial", panel_ids[2]: "denied"}
    verdict, _ = mgr7.submit_votes(ap.appeal_id, votes)

    check("T20.1 Partial reversal verdict", verdict.verdict_type == VerdictType.PARTIAL_REVERSAL)
    check("T20.2 Status is PARTIAL", ap.status == AppealStatus.PARTIAL)
    check("T20.3 Remedy has partial talent delta",
          abs(verdict.remedy["talent_delta"] - 0.2) < 0.001)
    check("T20.4 Restore type is partial_50pct",
          verdict.remedy["restore_type"] == "partial_50pct")

    # ── Summary ──────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Appeals Mechanism: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  FAILED: {failed}")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
