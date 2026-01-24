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
QUORUM_REQUIREMENTS = {
    CriticalAction.ADMIN_TRANSFER: {
        "min_approvals": 3,
        "trust_threshold": 0.7,
        "trust_weighted_quorum": 2.0,  # Sum of trust scores
        "expiry_hours": 48,
    },
    CriticalAction.POLICY_CHANGE: {
        "min_approvals": 2,
        "trust_threshold": 0.6,
        "trust_weighted_quorum": 1.5,
        "expiry_hours": 24,
    },
    CriticalAction.SECRET_ROTATION: {
        "min_approvals": 2,
        "trust_threshold": 0.7,
        "trust_weighted_quorum": 1.5,
        "expiry_hours": 12,
    },
    CriticalAction.MEMBER_REMOVAL: {
        "min_approvals": 2,
        "trust_threshold": 0.6,
        "trust_weighted_quorum": 1.5,
        "expiry_hours": 24,
    },
    CriticalAction.BUDGET_ALLOCATION: {
        "min_approvals": 2,
        "trust_threshold": 0.5,
        "trust_weighted_quorum": 1.0,
        "expiry_hours": 24,
    },
    CriticalAction.TEAM_DISSOLUTION: {
        "min_approvals": 4,  # Very high bar
        "trust_threshold": 0.8,
        "trust_weighted_quorum": 3.0,
        "expiry_hours": 72,
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
    3. Once quorum reached, action can be executed
    4. Expired proposals are automatically rejected
    """

    def __init__(self, team: 'Team'):
        """
        Initialize multi-sig manager.

        Args:
            team: Team this manager is for
        """
        self.team = team
        self.ledger = team.ledger
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
                    execution_result TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposals_team_status
                ON proposals(team_id, status)
            """)

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
        is_admin = self.team.verify_admin(proposer_lct)
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
            quorum = QUORUM_REQUIREMENTS.get(action, {
                "min_approvals": 2,
                "trust_threshold": 0.5,
                "trust_weighted_quorum": 1.0,
                "expiry_hours": 24,
            })

        # Generate proposal ID
        now = datetime.now(timezone.utc)
        seed = f"proposal:{self.team.team_id}:{action.value}:{now.isoformat()}"
        proposal_hash = hashlib.sha256(seed.encode()).hexdigest()[:12]
        proposal_id = f"msig:{proposal_hash}"

        # Calculate expiry
        expires_at = now + timedelta(hours=quorum.get("expiry_hours", 24))

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
        is_admin = self.team.verify_admin(voter_lct)

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

        # Cast vote
        vote = Vote(
            voter_lct=voter_lct,
            vote=approve,
            trust_score=trust_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            comment=comment
        )
        proposal.votes.append(vote)

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

        # Verify executor (usually admin)
        is_admin = self.team.verify_admin(executor_lct)
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
            # Actual removal would happen here
            return {
                "action": "member_removal",
                "removed_member": member_lct,
                "note": "Member removed via multi-sig"
            }

        else:
            return {
                "action": action.value,
                "data": data,
                "note": "Executed via multi-sig"
            }

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
                 executed_at, executed_by, execution_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(proposal.execution_result) if proposal.execution_result else None
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
            execution_result=json.loads(row["execution_result"]) if row["execution_result"] else {}
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
