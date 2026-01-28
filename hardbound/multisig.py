# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Multi-Signature Operations
# https://github.com/dp-web4/web4

"""
Multi-Signature: Critical operations requiring multiple witnesses.

For high-risk operations (admin transfer, policy changes, secret rotation),
single-party approval is insufficient. Multi-sig ensures:

1. **Quorum**: Minimum number of approvals required
2. **Trust-weighted**: Higher trust = more voting power
3. **Time-boxed**: Proposals expire if not approved in time
4. **Audit trail**: Full history of all votes

Critical actions requiring multi-sig:
- Admin transfer
- Policy modification (certain rules)
- Secret rotation
- Budget allocation above threshold
- Member removal
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Callable, TYPE_CHECKING
from enum import Enum
from pathlib import Path

if TYPE_CHECKING:
    from .team import Team
    from .federation import FederationRegistry
    from governance import Ledger


class ProposalStatus(Enum):
    """Status of a multi-sig proposal."""
    PENDING = "pending"      # Awaiting votes
    APPROVED = "approved"    # Quorum reached, can execute
    REJECTED = "rejected"    # Explicitly rejected
    EXPIRED = "expired"      # Time limit exceeded
    EXECUTED = "executed"    # Successfully executed
    FAILED = "failed"        # Execution failed


class CriticalAction(Enum):
    """Actions requiring multi-sig approval."""
    ADMIN_TRANSFER = "admin_transfer"
    POLICY_CHANGE = "policy_change"
    SECRET_ROTATION = "secret_rotation"
    MEMBER_REMOVAL = "member_removal"
    BUDGET_ALLOCATION = "budget_allocation"
    TEAM_DISSOLUTION = "team_dissolution"


# Default quorum requirements by action
# external_witness_required: minimum external witnesses needed (0 = none needed)
QUORUM_REQUIREMENTS = {
    CriticalAction.ADMIN_TRANSFER: {
        "min_approvals": 3,
        "trust_threshold": 0.7,
        "trust_weighted_quorum": 2.0,  # Sum of trust scores
        "expiry_hours": 48,
        "external_witness_required": 1,  # Must have outside validation
    },
    CriticalAction.POLICY_CHANGE: {
        "min_approvals": 2,
        "trust_threshold": 0.6,
        "trust_weighted_quorum": 1.5,
        "expiry_hours": 24,
        "external_witness_required": 0,
    },
    CriticalAction.SECRET_ROTATION: {
        "min_approvals": 2,
        "trust_threshold": 0.7,
        "trust_weighted_quorum": 1.5,
        "expiry_hours": 12,
        "external_witness_required": 0,
    },
    CriticalAction.MEMBER_REMOVAL: {
        "min_approvals": 2,
        "trust_threshold": 0.6,
        "trust_weighted_quorum": 1.5,
        "expiry_hours": 24,
        "external_witness_required": 0,
    },
    CriticalAction.BUDGET_ALLOCATION: {
        "min_approvals": 2,
        "trust_threshold": 0.5,
        "trust_weighted_quorum": 1.0,
        "expiry_hours": 24,
        "external_witness_required": 0,
    },
    CriticalAction.TEAM_DISSOLUTION: {
        "min_approvals": 4,  # Very high bar
        "trust_threshold": 0.8,
        "trust_weighted_quorum": 3.0,
        "expiry_hours": 72,
        "external_witness_required": 2,  # Requires 2 external witnesses
    },
}


@dataclass
class Vote:
    """A vote on a proposal."""
    voter_lct: str
    vote: bool  # True = approve, False = reject
    trust_score: float
    timestamp: str
    comment: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Proposal:
    """A multi-sig proposal for a critical action."""
    proposal_id: str
    team_id: str
    action: CriticalAction
    proposer_lct: str
    created_at: str
    expires_at: str

    # What the action will do
    action_data: Dict = field(default_factory=dict)
    description: str = ""

    # Voting state
    status: ProposalStatus = ProposalStatus.PENDING
    votes: List[Vote] = field(default_factory=list)

    # Quorum requirements
    min_approvals: int = 2
    trust_threshold: float = 0.5
    trust_weighted_quorum: float = 1.0

    # Execution result
    executed_at: Optional[str] = None
    executed_by: Optional[str] = None
    execution_result: Dict = field(default_factory=dict)

    # Security mitigations
    beneficiaries: List[str] = field(default_factory=list)
    min_voting_period_hours: float = 12.0
    vetoed_by: Optional[str] = None
    veto_reason: str = ""

    # Cross-team witnessing
    external_witness_required: int = 0  # Number of external witnesses needed
    external_witnesses: List[str] = field(default_factory=list)  # LCTs of external witnesses
    external_witness_teams: List[str] = field(default_factory=list)  # Team IDs of witnesses (parallel to external_witnesses)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["action"] = self.action.value
        d["status"] = self.status.value
        d["votes"] = [v.to_dict() if isinstance(v, Vote) else v for v in self.votes]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'Proposal':
        data = dict(data)
        data["action"] = CriticalAction(data["action"])
        data["status"] = ProposalStatus(data.get("status", "pending"))
        data["votes"] = [
            Vote(**v) if isinstance(v, dict) else v
            for v in data.get("votes", [])
        ]
        return cls(**data)

    @property
    def approval_count(self) -> int:
        """Count of approval votes."""
        return sum(1 for v in self.votes if v.vote)

    @property
    def rejection_count(self) -> int:
        """Count of rejection votes."""
        return sum(1 for v in self.votes if not v.vote)

    @property
    def trust_weighted_approvals(self) -> float:
        """Sum of trust scores for approval votes."""
        return sum(v.trust_score for v in self.votes if v.vote)

    def has_voted(self, lct: str) -> bool:
        """Check if an LCT has already voted."""
        return any(v.voter_lct == lct for v in self.votes)

    def is_expired(self) -> bool:
        """Check if proposal has expired."""
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return now > expires

    def check_quorum(self) -> tuple:
        """
        Check if quorum is reached.

        Returns:
            (reached: bool, reason: str)
        """
        if self.approval_count < self.min_approvals:
            return (False, f"Need {self.min_approvals} approvals, have {self.approval_count}")

        if self.trust_weighted_approvals < self.trust_weighted_quorum:
            return (False,
                f"Need trust-weighted quorum {self.trust_weighted_quorum}, "
                f"have {self.trust_weighted_approvals:.2f}")

        return (True, "Quorum reached")


class MultiSigManager:
    """
    Manages multi-signature proposals and voting.

    All critical operations flow through this manager:
    1. Proposer creates proposal
    2. Eligible voters cast votes
    3. Once quorum reached AND voting period elapsed, action can be executed
    4. Expired proposals are automatically rejected
    5. Conflict-of-interest detection flags self-benefiting proposals
    6. Veto mechanism allows high-trust members to block

    Security mitigations (2026-01-27):
    - Mandatory voting period before execution (prevents rush-through)
    - Conflict-of-interest detection (self-benefit raises quorum)
    - Veto power for members above veto_trust_threshold
    - Beneficiary exclusion from voting on self-benefiting proposals
    """

    # Minimum voting period before execution (hours)
    MIN_VOTING_PERIOD_HOURS = {
        CriticalAction.ADMIN_TRANSFER: 24,
        CriticalAction.POLICY_CHANGE: 12,
        CriticalAction.SECRET_ROTATION: 6,
        CriticalAction.MEMBER_REMOVAL: 12,
        CriticalAction.BUDGET_ALLOCATION: 12,
        CriticalAction.TEAM_DISSOLUTION: 48,
    }

    # Trust threshold for veto power
    VETO_TRUST_THRESHOLD = 0.85

    # Quorum multiplier when proposer is a beneficiary
    SELF_BENEFIT_QUORUM_MULTIPLIER = 1.5

    def __init__(self, team: 'Team', federation: 'FederationRegistry' = None):
        """
        Initialize multi-sig manager.

        Args:
            team: Team this manager is for
            federation: Optional FederationRegistry for cross-team validation
        """
        self.team = team
        self.ledger = team.ledger
        self.federation = federation
        self._ensure_table()

    def _ensure_table(self):
        """Create proposals table if not exists."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    proposer_lct TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    action_data TEXT NOT NULL,
                    description TEXT,
                    votes TEXT NOT NULL,
                    min_approvals INTEGER NOT NULL,
                    trust_threshold REAL NOT NULL,
                    trust_weighted_quorum REAL NOT NULL,
                    executed_at TEXT,
                    executed_by TEXT,
                    execution_result TEXT,
                    beneficiaries TEXT,
                    min_voting_period_hours REAL,
                    vetoed_by TEXT,
                    veto_reason TEXT,
                    external_witness_required INTEGER DEFAULT 0,
                    external_witnesses TEXT,
                    external_witness_teams TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposals_team_status
                ON proposals(team_id, status)
            """)
            # Schema migration: add columns that may not exist in older DBs
            for col_def in [
                ("beneficiaries", "TEXT"),
                ("min_voting_period_hours", "REAL"),
                ("vetoed_by", "TEXT"),
                ("veto_reason", "TEXT"),
                ("external_witness_required", "INTEGER DEFAULT 0"),
                ("external_witnesses", "TEXT"),
                ("external_witness_teams", "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE proposals ADD COLUMN {col_def[0]} {col_def[1]}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

    def create_proposal(
        self,
        proposer_lct: str,
        action: CriticalAction,
        action_data: Dict,
        description: str = "",
        custom_quorum: Optional[Dict] = None
    ) -> Proposal:
        """
        Create a new multi-sig proposal.

        Args:
            proposer_lct: LCT of the proposer (must be admin or trusted member)
            action: Critical action being proposed
            action_data: Data for the action (varies by action type)
            description: Human-readable description
            custom_quorum: Override default quorum requirements

        Returns:
            Proposal object

        Raises:
            PermissionError: If proposer lacks permission
            ValueError: If action data is invalid
        """
        # Verify proposer permission
        is_admin = self.team.is_admin(proposer_lct)
        member = self.team.get_member(proposer_lct)

        if not is_admin and not member:
            raise PermissionError("Proposer must be admin or team member")

        # For certain actions, only admin can propose
        admin_only_actions = {
            CriticalAction.TEAM_DISSOLUTION,
            CriticalAction.ADMIN_TRANSFER,
        }
        if action in admin_only_actions and not is_admin:
            raise PermissionError(f"Only admin can propose {action.value}")

        # Get quorum requirements
        if custom_quorum:
            quorum = custom_quorum
        else:
            quorum = dict(QUORUM_REQUIREMENTS.get(action, {
                "min_approvals": 2,
                "trust_threshold": 0.5,
                "trust_weighted_quorum": 1.0,
                "expiry_hours": 24,
            }))

        # MITIGATION: Conflict-of-interest detection
        # If proposer benefits from the action, raise the quorum
        beneficiaries = self._detect_beneficiaries(proposer_lct, action, action_data)
        is_self_benefiting = proposer_lct in beneficiaries

        if is_self_benefiting:
            quorum["min_approvals"] = max(
                quorum["min_approvals"],
                int(quorum["min_approvals"] * self.SELF_BENEFIT_QUORUM_MULTIPLIER)
            )
            quorum["trust_weighted_quorum"] = (
                quorum["trust_weighted_quorum"] * self.SELF_BENEFIT_QUORUM_MULTIPLIER
            )

        # Generate proposal ID
        now = datetime.now(timezone.utc)
        seed = f"proposal:{self.team.team_id}:{action.value}:{now.isoformat()}"
        proposal_hash = hashlib.sha256(seed.encode()).hexdigest()[:12]
        proposal_id = f"msig:{proposal_hash}"

        # Calculate expiry
        expires_at = now + timedelta(hours=quorum.get("expiry_hours", 24))

        # Determine minimum voting period
        min_voting_hours = self.MIN_VOTING_PERIOD_HOURS.get(action, 12)

        # Cross-team witnessing requirement
        ext_witness_req = quorum.get("external_witness_required", 0)

        proposal = Proposal(
            proposal_id=proposal_id,
            team_id=self.team.team_id,
            action=action,
            proposer_lct=proposer_lct,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            action_data=action_data,
            description=description,
            min_approvals=quorum["min_approvals"],
            trust_threshold=quorum["trust_threshold"],
            trust_weighted_quorum=quorum["trust_weighted_quorum"],
            beneficiaries=beneficiaries,
            min_voting_period_hours=min_voting_hours,
            external_witness_required=ext_witness_req,
        )

        # Store proposal
        self._save_proposal(proposal)

        # Audit trail
        self.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="multisig_proposal_created",
            tool_name="hardbound",
            target=proposal_id,
            r6_data={
                "action": action.value,
                "proposer": proposer_lct,
                "description": description,
                "quorum": quorum,
                "expires_at": expires_at.isoformat()
            }
        )

        return proposal

    def vote(
        self,
        proposal_id: str,
        voter_lct: str,
        approve: bool,
        comment: str = ""
    ) -> Proposal:
        """
        Cast a vote on a proposal.

        Args:
            proposal_id: ID of the proposal
            voter_lct: LCT of the voter
            approve: True to approve, False to reject
            comment: Optional comment explaining vote

        Returns:
            Updated proposal

        Raises:
            ValueError: If proposal not found or invalid state
            PermissionError: If voter lacks permission
        """
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        # Check proposal state
        if proposal.status != ProposalStatus.PENDING:
            raise ValueError(f"Proposal not pending: {proposal.status.value}")

        if proposal.is_expired():
            proposal.status = ProposalStatus.EXPIRED
            self._save_proposal(proposal)
            raise ValueError("Proposal has expired")

        # Verify voter is eligible
        member = self.team.get_member(voter_lct)
        is_admin = self.team.is_admin(voter_lct)

        if not member and not is_admin:
            raise PermissionError("Voter must be admin or team member")

        # Check trust threshold
        trust_score = self.team.get_member_trust_score(voter_lct)
        if trust_score < proposal.trust_threshold:
            raise PermissionError(
                f"Insufficient trust: {trust_score:.2f} < {proposal.trust_threshold}"
            )

        # Check for existing vote
        if proposal.has_voted(voter_lct):
            raise ValueError("Already voted on this proposal")

        # Cannot vote on own proposal for critical actions
        if voter_lct == proposal.proposer_lct:
            raise PermissionError("Cannot vote on your own proposal")

        # MITIGATION: Beneficiary exclusion
        # Members who benefit from the proposal cannot approve it
        if voter_lct in proposal.beneficiaries and approve:
            raise PermissionError(
                "Beneficiaries cannot approve proposals they benefit from. "
                f"Detected beneficiary: {voter_lct}"
            )

        # Cast vote
        vote = Vote(
            voter_lct=voter_lct,
            vote=approve,
            trust_score=trust_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            comment=comment
        )
        proposal.votes.append(vote)

        # MITIGATION: Veto power for high-trust members
        # A single rejection from a high-trust member vetoes the proposal
        if not approve and trust_score >= self.VETO_TRUST_THRESHOLD:
            proposal.status = ProposalStatus.REJECTED
            proposal.vetoed_by = voter_lct
            proposal.veto_reason = comment or f"Vetoed by high-trust member (trust={trust_score:.3f})"
            self._save_proposal(proposal)
            self.ledger.record_audit(
                session_id=self.team.team_id,
                action_type="multisig_vetoed",
                tool_name="hardbound",
                target=proposal.proposal_id,
                r6_data={
                    "vetoed_by": voter_lct,
                    "trust_score": trust_score,
                    "reason": proposal.veto_reason,
                }
            )
            return proposal

        # Check quorum
        quorum_reached, reason = proposal.check_quorum()
        if quorum_reached:
            proposal.status = ProposalStatus.APPROVED

        # Check for rejection (majority reject)
        if proposal.rejection_count > len(self.team.list_members()) // 2:
            proposal.status = ProposalStatus.REJECTED

        # Save and audit
        self._save_proposal(proposal)

        self.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="multisig_vote",
            tool_name="hardbound",
            target=proposal_id,
            r6_data={
                "voter": voter_lct,
                "approve": approve,
                "trust_score": trust_score,
                "comment": comment,
                "status": proposal.status.value,
                "approval_count": proposal.approval_count,
                "trust_weighted": proposal.trust_weighted_approvals
            }
        )

        return proposal

    def add_external_witness(
        self,
        proposal_id: str,
        witness_lct: str,
        witness_team_id: str,
        witness_trust_score: float,
        attestation: str = "",
    ) -> Proposal:
        """
        Add an external witness to a proposal requiring cross-team validation.

        External witnesses are members of OTHER teams who attest that the
        proposed action is legitimate. This prevents insular team capture
        where a compromised team approves its own destructive actions.

        Args:
            proposal_id: ID of the proposal
            witness_lct: LCT of the external witness
            witness_team_id: Team ID the witness belongs to (must differ from proposal team)
            witness_trust_score: Trust score of the witness in their own team
            attestation: Optional attestation message

        Returns:
            Updated proposal

        Raises:
            ValueError: If proposal not found, expired, or witness is internal
            PermissionError: If witness trust is insufficient
        """
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if proposal.status not in (ProposalStatus.PENDING, ProposalStatus.APPROVED):
            raise ValueError(f"Cannot witness proposal in state: {proposal.status.value}")

        if proposal.is_expired():
            proposal.status = ProposalStatus.EXPIRED
            self._save_proposal(proposal)
            raise ValueError("Proposal has expired")

        if proposal.external_witness_required == 0:
            raise ValueError("This proposal does not require external witnesses")

        # External witness must NOT be from this team
        if witness_team_id == self.team.team_id:
            raise ValueError(
                "External witness must be from a different team. "
                f"Witness team '{witness_team_id}' matches proposal team."
            )

        # Must not be a member of this team either (belt AND suspenders)
        if self.team.get_member(witness_lct) is not None:
            raise ValueError(
                f"Witness '{witness_lct}' is a member of this team. "
                "External witnesses must be from outside the team."
            )

        # Minimum trust threshold for external witnesses (same as proposal threshold)
        if witness_trust_score < proposal.trust_threshold:
            raise PermissionError(
                f"External witness trust {witness_trust_score:.2f} below "
                f"threshold {proposal.trust_threshold:.2f}"
            )

        # No duplicate witnesses
        if witness_lct in proposal.external_witnesses:
            raise ValueError(f"Witness '{witness_lct}' has already attested")

        # DIVERSITY REQUIREMENT: Each external witness must come from a DIFFERENT team.
        # This prevents collusion where one team provides all external witnesses.
        if witness_team_id in proposal.external_witness_teams:
            raise ValueError(
                f"Team '{witness_team_id}' has already provided a witness. "
                "Each external witness must come from a different team "
                "to prevent cross-team collusion."
            )

        # FEDERATION VALIDATION: If federation registry is available, verify
        # the witness team is registered, active, and has acceptable reputation
        if self.federation:
            fed_team = self.federation.get_team(witness_team_id)
            if not fed_team:
                raise ValueError(
                    f"Witness team '{witness_team_id}' is not registered in the federation. "
                    "External witnesses must come from federated teams."
                )
            if fed_team.status.value != "active":
                raise ValueError(
                    f"Witness team '{witness_team_id}' is {fed_team.status.value}. "
                    "Only active federated teams can provide witnesses."
                )
            from .federation import FederationRegistry
            if fed_team.witness_score < FederationRegistry.MIN_WITNESS_SCORE:
                raise PermissionError(
                    f"Witness team '{witness_team_id}' has low reputation "
                    f"({fed_team.witness_score:.2f} < {FederationRegistry.MIN_WITNESS_SCORE}). "
                    "Team must improve witness reputation before providing witnesses."
                )

            # Record the witness event in federation
            self.federation.record_witness_event(
                witness_team_id=witness_team_id,
                proposal_team_id=self.team.team_id,
                witness_lct=witness_lct,
                proposal_id=proposal_id,
            )

        # Record the external witness and their team
        proposal.external_witnesses.append(witness_lct)
        proposal.external_witness_teams.append(witness_team_id)
        self._save_proposal(proposal)

        # Audit trail
        self.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="multisig_external_witness",
            tool_name="hardbound",
            target=proposal_id,
            r6_data={
                "witness_lct": witness_lct,
                "witness_team": witness_team_id,
                "witness_trust": witness_trust_score,
                "attestation": attestation,
                "witnesses_count": len(proposal.external_witnesses),
                "witnesses_required": proposal.external_witness_required,
            }
        )

        return proposal

    def request_external_witnesses(
        self,
        proposal_id: str,
        count: int = None,
        seed: int = None,
    ) -> List[dict]:
        """
        Auto-select and request external witnesses from the federation.

        Uses the federation's reputation-weighted random selection to pick
        witnesses from qualified teams. Returns the selected teams for
        the caller to coordinate the actual witnessing (e.g., send notifications).

        Args:
            proposal_id: ID of the proposal needing witnesses
            count: Number of witnesses to request (defaults to external_witness_required)
            seed: Optional random seed for reproducibility (testing)

        Returns:
            List of dicts with team info for selected witnesses

        Raises:
            ValueError: If no federation, proposal not found, or no candidates
        """
        if not self.federation:
            raise ValueError("No federation configured for witness selection")

        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if proposal.external_witness_required == 0:
            raise ValueError("This proposal does not require external witnesses")

        needed = count if count is not None else proposal.external_witness_required
        already_have = len(proposal.external_witnesses)
        to_select = max(0, needed - already_have)

        if to_select == 0:
            return []  # Already have enough witnesses

        # Select witnesses from federation
        selected_teams = self.federation.select_witnesses(
            requesting_team_id=self.team.team_id,
            count=to_select,
            min_score=proposal.trust_threshold,
            seed=seed,
        )

        if not selected_teams:
            raise ValueError(
                f"No qualified witnesses found in federation (need {to_select}, "
                f"min_score={proposal.trust_threshold})"
            )

        # Record the request in audit trail
        selected_info = []
        for fedteam in selected_teams:
            info = {
                "team_id": fedteam.team_id,
                "team_name": fedteam.name,
                "witness_score": fedteam.witness_score,
                "domains": fedteam.domains,
            }
            selected_info.append(info)

        self.team.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="witnesses_requested",
            tool_name="hardbound",
            target=proposal_id,
            r6_data={
                "proposal_id": proposal_id,
                "witnesses_needed": to_select,
                "witnesses_selected": len(selected_info),
                "selected_teams": selected_info,
            }
        )

        return selected_info

    def execute_proposal(
        self,
        proposal_id: str,
        executor_lct: str,
        execution_callback: Optional[Callable] = None
    ) -> Proposal:
        """
        Execute an approved proposal.

        Args:
            proposal_id: ID of the proposal
            executor_lct: LCT executing the proposal (usually admin)
            execution_callback: Optional callback to perform the action

        Returns:
            Updated proposal

        Raises:
            ValueError: If proposal not approved
            PermissionError: If executor lacks permission
        """
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Proposal not approved: {proposal.status.value}")

        # MITIGATION: Mandatory voting period
        # Cannot execute until minimum voting period has elapsed
        created = datetime.fromisoformat(proposal.created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed_hours = (now - created).total_seconds() / 3600
        if elapsed_hours < proposal.min_voting_period_hours:
            remaining = proposal.min_voting_period_hours - elapsed_hours
            raise ValueError(
                f"Voting period not elapsed. {remaining:.1f}h remaining "
                f"(minimum {proposal.min_voting_period_hours}h required)"
            )

        # MITIGATION: Cross-team witnessing enforcement
        # Critical actions require external witnesses before execution
        if proposal.external_witness_required > 0:
            witness_count = len(proposal.external_witnesses)
            if witness_count < proposal.external_witness_required:
                raise ValueError(
                    f"Insufficient external witnesses: {witness_count} present, "
                    f"{proposal.external_witness_required} required. "
                    "Cross-team validation is mandatory for this action."
                )

        # Verify executor (usually admin)
        is_admin = self.team.is_admin(executor_lct)
        if not is_admin:
            raise PermissionError("Only admin can execute proposals")

        # Execute the action
        try:
            if execution_callback:
                result = execution_callback(proposal.action, proposal.action_data)
            else:
                result = self._default_execute(proposal)

            proposal.status = ProposalStatus.EXECUTED
            proposal.executed_at = datetime.now(timezone.utc).isoformat()
            proposal.executed_by = executor_lct
            proposal.execution_result = result if isinstance(result, dict) else {"result": str(result)}

        except Exception as e:
            proposal.status = ProposalStatus.FAILED
            proposal.executed_at = datetime.now(timezone.utc).isoformat()
            proposal.executed_by = executor_lct
            proposal.execution_result = {"error": str(e)}

        self._save_proposal(proposal)

        # FEDERATION FEEDBACK: Update witness reputation based on outcome
        if self.federation and proposal.external_witnesses:
            outcome = "succeeded" if proposal.status == ProposalStatus.EXECUTED else "failed"
            self.federation.update_witness_outcome(proposal.proposal_id, outcome)

        self.ledger.record_audit(
            session_id=self.team.team_id,
            action_type="multisig_executed",
            tool_name="hardbound",
            target=proposal_id,
            r6_data={
                "executor": executor_lct,
                "status": proposal.status.value,
                "action": proposal.action.value,
                "result": proposal.execution_result
            }
        )

        return proposal

    def _default_execute(self, proposal: Proposal) -> dict:
        """
        Default execution for known action types.

        Returns:
            Execution result dict
        """
        action = proposal.action
        data = proposal.action_data

        if action == CriticalAction.ADMIN_TRANSFER:
            new_admin = data.get("new_admin_lct")
            if not new_admin:
                raise ValueError("new_admin_lct required")
            # This would actually transfer admin
            # For now, just return success (actual transfer needs binding)
            return {
                "action": "admin_transfer",
                "new_admin": new_admin,
                "note": "Admin transfer requires manual binding update"
            }

        elif action == CriticalAction.POLICY_CHANGE:
            # Policy changes would be applied here
            return {
                "action": "policy_change",
                "changes": data.get("changes", {}),
                "note": "Policy updated via multi-sig"
            }

        elif action == CriticalAction.MEMBER_REMOVAL:
            member_lct = data.get("member_lct")
            if not member_lct:
                raise ValueError("member_lct required")
            # Execute actual removal through Team.remove_member()
            result = self.team.remove_member(
                lct_id=member_lct,
                reason=data.get("reason", "Removed via multi-sig"),
                via_multisig=proposal.proposal_id,
            )
            return {
                "action": "member_removal",
                "removed_member": member_lct,
                **result,
            }

        else:
            return {
                "action": action.value,
                "data": data,
                "note": "Executed via multi-sig"
            }

    def _detect_beneficiaries(self, proposer_lct: str, action: CriticalAction,
                              action_data: Dict) -> List[str]:
        """
        Detect which LCTs benefit from a proposal.

        This is the conflict-of-interest detector. It examines the action data
        to identify members who would directly benefit if the proposal executes.
        """
        beneficiaries = []

        if action == CriticalAction.BUDGET_ALLOCATION:
            # Who receives the budget?
            recipient = action_data.get("recipient")
            if recipient:
                beneficiaries.append(recipient)
            recipients = action_data.get("recipients", [])
            beneficiaries.extend(recipients)

        elif action == CriticalAction.ADMIN_TRANSFER:
            # Who becomes admin?
            new_admin = action_data.get("new_admin_lct")
            if new_admin:
                beneficiaries.append(new_admin)

        elif action == CriticalAction.MEMBER_REMOVAL:
            # Who might benefit from removal? (competitors for role)
            # The proposer might benefit if they take over the removed member's role
            # For now, just flag the proposer if they're not the one being removed
            removed = action_data.get("member_lct")
            if removed and removed != proposer_lct:
                # Proposer might benefit from removing a competitor
                beneficiaries.append(proposer_lct)

        elif action == CriticalAction.POLICY_CHANGE:
            # Check if changes lower thresholds for specific roles
            changes = action_data.get("changes", {})
            # If changes reduce trust thresholds, the proposer benefits
            for key, value in changes.items():
                if "threshold" in key.lower() and isinstance(value, (int, float)):
                    # Proposer benefits from lowered thresholds
                    beneficiaries.append(proposer_lct)
                    break

        return list(set(beneficiaries))  # Deduplicate

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a proposal by ID."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?",
                (proposal_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_proposal(row)

    def get_pending_proposals(self) -> List[Proposal]:
        """Get all pending proposals for this team."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM proposals WHERE team_id = ? AND status = ?",
                (self.team.team_id, ProposalStatus.PENDING.value)
            ).fetchall()

            proposals = []
            for row in rows:
                proposal = self._row_to_proposal(row)
                # Check expiry
                if proposal.is_expired():
                    proposal.status = ProposalStatus.EXPIRED
                    self._save_proposal(proposal)
                else:
                    proposals.append(proposal)

            return proposals

    def get_proposal_history(self, limit: int = 50) -> List[Proposal]:
        """Get proposal history for this team."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM proposals
                   WHERE team_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (self.team.team_id, limit)
            ).fetchall()

            return [self._row_to_proposal(row) for row in rows]

    def _save_proposal(self, proposal: Proposal):
        """Save proposal to database."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO proposals
                (proposal_id, team_id, action, proposer_lct, created_at,
                 expires_at, status, action_data, description, votes,
                 min_approvals, trust_threshold, trust_weighted_quorum,
                 executed_at, executed_by, execution_result,
                 beneficiaries, min_voting_period_hours, vetoed_by, veto_reason,
                 external_witness_required, external_witnesses, external_witness_teams)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.proposal_id,
                proposal.team_id,
                proposal.action.value,
                proposal.proposer_lct,
                proposal.created_at,
                proposal.expires_at,
                proposal.status.value,
                json.dumps(proposal.action_data),
                proposal.description,
                json.dumps([v.to_dict() if isinstance(v, Vote) else v for v in proposal.votes]),
                proposal.min_approvals,
                proposal.trust_threshold,
                proposal.trust_weighted_quorum,
                proposal.executed_at,
                proposal.executed_by,
                json.dumps(proposal.execution_result) if proposal.execution_result else None,
                json.dumps(proposal.beneficiaries),
                proposal.min_voting_period_hours,
                proposal.vetoed_by,
                proposal.veto_reason,
                proposal.external_witness_required,
                json.dumps(proposal.external_witnesses),
                json.dumps(proposal.external_witness_teams),
            ))

    def _row_to_proposal(self, row) -> Proposal:
        """Convert database row to Proposal object."""
        return Proposal(
            proposal_id=row["proposal_id"],
            team_id=row["team_id"],
            action=CriticalAction(row["action"]),
            proposer_lct=row["proposer_lct"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            action_data=json.loads(row["action_data"]),
            description=row["description"] or "",
            status=ProposalStatus(row["status"]),
            votes=[Vote(**v) for v in json.loads(row["votes"])],
            min_approvals=row["min_approvals"],
            trust_threshold=row["trust_threshold"],
            trust_weighted_quorum=row["trust_weighted_quorum"],
            executed_at=row["executed_at"],
            executed_by=row["executed_by"],
            execution_result=json.loads(row["execution_result"]) if row["execution_result"] else {},
            beneficiaries=json.loads(row["beneficiaries"]) if row["beneficiaries"] else [],
            min_voting_period_hours=row["min_voting_period_hours"] if row["min_voting_period_hours"] is not None else 12.0,
            vetoed_by=row["vetoed_by"],
            veto_reason=row["veto_reason"] or "",
            external_witness_required=row["external_witness_required"] if row["external_witness_required"] is not None else 0,
            external_witnesses=json.loads(row["external_witnesses"]) if row["external_witnesses"] else [],
            external_witness_teams=json.loads(row["external_witness_teams"]) if row["external_witness_teams"] else [],
        )


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Sig Module - Quorum Requirements")
    print("=" * 60)

    for action, quorum in QUORUM_REQUIREMENTS.items():
        print(f"\n{action.value}:")
        print(f"  Min approvals: {quorum['min_approvals']}")
        print(f"  Trust threshold: {quorum['trust_threshold']}")
        print(f"  Trust-weighted quorum: {quorum['trust_weighted_quorum']}")
        print(f"  Expiry: {quorum['expiry_hours']} hours")
        ext = quorum.get('external_witness_required', 0)
        if ext > 0:
            print(f"  External witnesses required: {ext}")
